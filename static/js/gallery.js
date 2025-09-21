function updateCreateButton() {
  const checkboxes = document.querySelectorAll(".image-checkbox:checked")
  const createBtn = document.getElementById("createVideoBtn")

  if (checkboxes.length > 0) {
    createBtn.disabled = false
    createBtn.innerHTML = `<i class="fas fa-video"></i> Create Video (${checkboxes.length} images)`
  } else {
    createBtn.disabled = true
    createBtn.innerHTML = '<i class="fas fa-video"></i> Create Video'
  }
}

function deleteImage(imageId) {
  if (confirm("Are you sure you want to delete this image?")) {
    const form = document.getElementById("deleteForm")
    form.action = `/delete_image/${imageId}`
    form.submit()
  }
}

function showNotification(message, type) {
  console.log(`Notification: ${message} (Type: ${type})`)
}

function showLoading(button) {
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...'
}

document.addEventListener("DOMContentLoaded", () => {
  const videoForm = document.getElementById("videoForm")

  if (videoForm) {
    videoForm.addEventListener("submit", function (e) {
      const checkboxes = document.querySelectorAll(".image-checkbox:checked")

      if (checkboxes.length === 0) {
        e.preventDefault()
        showNotification("Please select at least one image to create a video.", "error")
        return
      }

      const submitBtn = this.querySelector('button[type="submit"]')
      const originalText = submitBtn.innerHTML
      showLoading(submitBtn)

      showNotification("Creating your video... This may take a few minutes.", "info")
    })
  }

  updateCreateButton()
})

function showLoadingScreen() {
  const modal = document.getElementById("loadingModal");
  const texts = [
    "Cooking up your slideshow... 🧑‍🍳",
    "Adding extra sparkle... ✨",
    "Mixing your memories... 🥣",
    "Summoning the video gods... 🧙‍♂️",
    "Hang tight, magic in progress! 🪄"
  ];
  document.getElementById("loadingText").innerText = texts[Math.floor(Math.random() * texts.length)];
  modal.style.display = "flex";
}

document.addEventListener("DOMContentLoaded", () => {
  const videoForm = document.getElementById("videoForm");
  if (videoForm) {
    videoForm.addEventListener("submit", function (e) {
      showLoadingScreen();
    });
  }
  updateCreateButton();
});
