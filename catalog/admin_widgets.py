from __future__ import annotations

from django import forms
from django.utils.safestring import mark_safe


class CloudinaryPublicIdWidget(forms.TextInput):
    """
    Widget لاختيار صورة من مكتبة Cloudinary عبر public_id.
    - يعتمد على نص (public_id) مثل: media/django_test/test_e0oqj9
    - لا يرفع ملف، فقط يختار من المكتبة
    """

    def render(self, name, value, attrs=None, renderer=None):
        # هذا يرجع input text طبيعي (وله template_name صحيح)
        input_html = super().render(name, value, attrs, renderer)

        # زر يفتح Cloudinary Console (اختيار يدوي) + تلميح
        help_html = """
        <div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <a class="button" target="_blank" rel="noopener"
             href="https://console.cloudinary.com/console/media_library/folders/all">
             فتح مكتبة Cloudinary
          </a>
          <span style="color:#666;font-size:12px">
            انسخ <b>Public ID</b> من Cloudinary وضعه هنا (بدون https://res.cloudinary.com)
          </span>
        </div>
        """

        example_html = """
        <div style="margin-top:8px;color:#777;font-size:12px;line-height:1.6">
          مثال Public ID:
          <code>media/django_test/test_e0oqj9</code>
        </div>
        """

        return mark_safe(input_html + help_html + example_html)
