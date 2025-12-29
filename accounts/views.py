from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from .models import CustomerProfile, phone_validator  # ✅ من موديلك

logger = logging.getLogger(__name__)
User = get_user_model()


def signup_view(request):
    """
    إنشاء حساب جديد + إنشاء CustomerProfile تلقائيًا.
    """
    if request.user.is_authenticated:
        return redirect("shop:home") if _has_url("shop:home") else redirect("/")

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        phone = (request.POST.get("phone") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""
        marketing = request.POST.get("marketing") == "on"

        errors: list[str] = []
        if not full_name:
            errors.append(_("الاسم الكامل مطلوب."))
        if not username:
            errors.append(_("اسم المستخدم مطلوب."))
        if not email:
            errors.append(_("البريد الإلكتروني مطلوب."))
        if not password1 or not password2:
            errors.append(_("كلمة المرور مطلوبة."))
        if password1 != password2:
            errors.append(_("كلمتا المرور غير متطابقتين."))

        # ✅ تحقق رقم الجوال (اختياري لكن إن وُجد يجب أن يطابق)
        if phone:
            try:
                phone_validator(phone)
            except ValidationError as e:
                errors.append(e.messages[0] if e.messages else _("رقم الجوال غير صحيح."))

        # ✅ تحقق سياسة كلمات المرور
        if password1 and not errors:
            try:
                validate_password(password1)
            except ValidationError as e:
                errors.extend(e.messages)

        # ✅ تحقق عدم التكرار (email/username)
        if email and User.objects.filter(email__iexact=email).exists():
            errors.append(_("البريد الإلكتروني مستخدم مسبقًا."))
        if username and User.objects.filter(username__iexact=username).exists():
            errors.append(_("اسم المستخدم مستخدم مسبقًا."))

        if errors:
            for msg in errors:
                messages.error(request, msg)
            return render(
                request,
                "accounts_templates/signup.html",
                {
                    "full_name": full_name,
                    "username": username,
                    "email": email,
                    "phone": phone,
                    "marketing": marketing,
                },
            )

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                )

                # الاسم الكامل: نحاول تخزينه حسب الحقول المتاحة
                if hasattr(user, "first_name") and hasattr(user, "last_name"):
                    parts = full_name.split()
                    user.first_name = parts[0]
                    user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                    user.save(update_fields=["first_name", "last_name"])

                CustomerProfile.objects.create(
                    user=user,
                    phone=phone,
                    is_marketing_opt_in=marketing,
                )

        except IntegrityError:
            logger.exception("IntegrityError while creating user/profile")
            messages.error(request, _("حدث تعارض أثناء إنشاء الحساب. جرّب بيانات مختلفة."))
            return render(request, "accounts_templates/signup.html")

        login(request, user)
        messages.success(request, _("تم إنشاء الحساب بنجاح!"))
        return redirect("shop:home") if _has_url("shop:home") else redirect("/")

    return render(request, "accounts_templates/signup.html")


def login_view(request):
    """
    تسجيل دخول عبر:
    - username أو email أو phone (من CustomerProfile.phone)
    """
    if request.user.is_authenticated:
        return redirect("shop:home") if _has_url("shop:home") else redirect("/")

    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        password = request.POST.get("password") or ""
        remember = request.POST.get("remember") == "on"

        if not identifier or not password:
            messages.error(request, _("أدخل بيانات الدخول كاملة."))
            return render(
                request,
                "accounts_templates/login.html",
                {"identifier": identifier, "remember": remember},
            )

        user = _resolve_user_from_identifier(identifier)
        if not user:
            messages.error(request, _("بيانات الدخول غير صحيحة."))
            return render(
                request,
                "accounts_templates/login.html",
                {"identifier": identifier, "remember": remember},
            )

        auth_user = authenticate(request, username=user.username, password=password)
        if not auth_user:
            messages.error(request, _("بيانات الدخول غير صحيحة."))
            return render(
                request,
                "accounts_templates/login.html",
                {"identifier": identifier, "remember": remember},
            )

        login(request, auth_user)

        # ✅ تذكرني: إذا لم يحدد، نخلي الجلسة تنتهي بإغلاق المتصفح
        if not remember:
            request.session.set_expiry(0)

        messages.success(request, _("تم تسجيل الدخول بنجاح."))
        return redirect("shop:home") if _has_url("shop:home") else redirect("/")

    return render(request, "accounts_templates/login.html")


def logout_view(request):
    """
    تسجيل خروج آمن (POST فقط) ثم إعادة توجيه للرئيسية.
    """
    if request.method == "POST":
        logout(request)
    return redirect("shop:home") if _has_url("shop:home") else redirect("/")


# ---------------- Helpers ----------------

def _resolve_user_from_identifier(identifier: str):
    """
    يحاول إيجاد المستخدم من:
    - email
    - username
    - phone (CustomerProfile.phone)
    """
    # email
    if "@" in identifier:
        return User.objects.filter(email__iexact=identifier).first()

    # phone (لو كان رقم)
    if identifier.replace("+", "").isdigit():
        profile = CustomerProfile.objects.select_related("user").filter(phone=identifier).first()
        if profile:
            return profile.user

    # username
    return User.objects.filter(username__iexact=identifier).first()


def _has_url(viewname: str) -> bool:
    """
    محاولة آمنة لمعرفة هل يوجد مسار مسمى.
    """
    try:
        from django.urls import reverse
        reverse(viewname)
        return True
    except Exception:
        return False
