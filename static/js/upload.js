let selectedFiles = []
let imageDataArray = []

function showNotification(message, type) {
  console.log(`Notification (${type}): ${message}`)
}

function showLoading(button) {
  button.innerHTML = "Loading..."
}

document.addEventListener("DOMContentLoaded", () => {
  const uploadZone = document.getElementById("uploadZone")
  const fileInput = document.getElementById("fileInput")
  const uploadPreview = document.getElementById("uploadPreview")
  const previewGrid = document.getElementById("previewGrid")
  const imageDataInput = document.getElementById("imageData")
  const uploadForm = document.getElementById("uploadForm")

  // Click to browse files
  uploadZone.addEventListener("click", () => {
    fileInput.click()
  })

  // File input change
  fileInput.addEventListener("change", handleFiles)

  // Drag and drop functionality
  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault()
    uploadZone.classList.add("dragover")
  })

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("dragover")
  })

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault()
    uploadZone.classList.remove("dragover")
    const files = Array.from(e.dataTransfer.files)
    handleFiles({ target: { files } })
  })

  // Form submission
  uploadForm.addEventListener("submit", (e) => {
    e.preventDefault()
    if (imageDataArray.length === 0) {
      showNotification("Please select at least one image.", "error")
      return
    }

    // Join image data with $ separator
    imageDataInput.value = imageDataArray.join("$")

    // Show loading state
    const submitBtn = uploadForm.querySelector('button[type="submit"]')
    const originalText = submitBtn.innerHTML
    showLoading(submitBtn)

    uploadForm.submit()
  })

  function handleFiles(event) {
    const files = Array.from(event.target.files)
    const validFiles = files.filter((file) => file.type.startsWith("image/"))

    if (validFiles.length === 0) {
      showNotification("Please select valid image files.", "error")
      return
    }

    validFiles.forEach((file) => {
      if (selectedFiles.find((f) => f.name === file.name && f.size === file.size)) {
        return
      }

      selectedFiles.push(file)

      const reader = new FileReader()
      reader.onload = (e) => {
        const dataUrl = e.target.result
        imageDataArray.push(dataUrl)

        const previewItem = document.createElement("div")
        previewItem.className = "preview-item"
        previewItem.innerHTML = `
                    <img src="${dataUrl}" alt="Preview">
                    <button type="button" class="preview-remove" onclick="removeImage(${selectedFiles.length - 1})">
                        <i class="fas fa-times"></i>
                    </button>
                `

        previewGrid.appendChild(previewItem)
        uploadPreview.style.display = "block"
      }

      reader.readAsDataURL(file)
    })
  }
})

function removeImage(index) {
  selectedFiles.splice(index, 1)
  imageDataArray.splice(index, 1)

  const previewGrid = document.getElementById("previewGrid")
  previewGrid.innerHTML = ""

  imageDataArray.forEach((dataUrl, i) => {
    const previewItem = document.createElement("div")
    previewItem.className = "preview-item"
    previewItem.innerHTML = `
            <img src="${dataUrl}" alt="Preview">
            <button type="button" class="preview-remove" onclick="removeImage(${i})">
                <i class="fas fa-times"></i>
            </button>
        `
    previewGrid.appendChild(previewItem)
  })

  if (selectedFiles.length === 0) {
    document.getElementById("uploadPreview").style.display = "none"
  }
}

function clearImages() {
  selectedFiles = []
  imageDataArray = []
  document.getElementById("previewGrid").innerHTML = ""
  document.getElementById("uploadPreview").style.display = "none"
  document.getElementById("fileInput").value = ""
}
