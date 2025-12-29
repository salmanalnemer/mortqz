(function () {
  function init() {
    const buttons = document.querySelectorAll('button[id^="btn_"][data-cloud-name][data-preview]');
    buttons.forEach((btn) => {
      if (btn.dataset.bound === "1") return;
      btn.dataset.bound = "1";

      btn.addEventListener("click", function () {
        const cloudName = btn.getAttribute("data-cloud-name");
        const targetId = btn.getAttribute("data-target");
        const previewId = btn.getAttribute("data-preview");
        const input = document.getElementById(targetId);
        const preview = document.getElementById(previewId);

        if (!input) {
          alert("لم يتم العثور على حقل الإدخال.");
          return;
        }

        if (!window.cloudinary || !window.cloudinary.createMediaLibrary) {
          alert("Cloudinary Media Library لم يتم تحميله. تأكد من الاتصال بالإنترنت.");
          return;
        }

        const ml = window.cloudinary.createMediaLibrary(
          {
            cloud_name: cloudName,
            multiple: false,
            max_files: 1,
          },
          {
            insertHandler: function (data) {
              const asset = (data && data.assets && data.assets[0]) ? data.assets[0] : null;
              if (!asset) return;

              // public_id مثل: products/abc123
              input.value = asset.public_id;

              // معاينة
              if (preview) {
                preview.src = asset.secure_url;
                preview.style.display = "inline-block";
              }
            },
          },
          "#"
        );

        ml.show();
      });
    });
  }

  // Admin pages load dynamically sometimes
  document.addEventListener("DOMContentLoaded", init);
  document.addEventListener("formset:added", init);
})();
