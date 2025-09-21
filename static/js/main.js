document.addEventListener("DOMContentLoaded", () => {
  // Auto-hide flash messages after 5 seconds
  const flashMessages = document.querySelectorAll(".flash-message")
  flashMessages.forEach((message) => {
    setTimeout(() => {
      message.style.opacity = "0"
      setTimeout(() => {
        message.remove()
      }, 300)
    }, 5000)
  })

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute("href"))
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
      }
    })
  })
})

function showLoading(element) {
  element.disabled = true
  element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...'
}

function hideLoading(element, originalText) {
  element.disabled = false
  element.innerHTML = originalText
}

function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `flash-message flash-${type}`
  notification.innerHTML = `
        <i class="fas fa-${type === "error" ? "exclamation-circle" : type === "success" ? "check-circle" : "info-circle"}"></i>
        ${message}
        <button class="flash-close" onclick="this.parentElement.remove()">×</button>
    `

  const container = document.querySelector(".flash-messages") || document.querySelector(".main-content")
  container.insertBefore(notification, container.firstChild)

  setTimeout(() => {
    notification.remove()
  }, 5000)
}
