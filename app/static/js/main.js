async function requestJSON(url, method, body) {
  if (method === undefined) {
    method = "GET"
  }
  if (body === undefined) {
    body = null
  }
  
  const options = {}
  options.method = method
  options.headers = {}
  
  if (body !== null) {
    options.headers["Content-Type"] = "application/json"
    options.body = JSON.stringify(body)
  }
  
  const res = await fetch(url, options)
  const data = await res.json()
  if (!res.ok) {
    let errorMsg = "Request failed"
    if (data.error) {
      errorMsg = data.error
    }
    throw new Error(errorMsg)
  }
  return data
}

function getAuthMode() {
  return document.body?.dataset?.authMode || "any"
}

function authRedirectTarget(sessionData) {
  return "/chat"
}

async function fetchSessionState() {
  try {
    const res = await fetch("/api/auth/session", {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
    })
    if (!res.ok) {
      return { authenticated: false }
    }
    return await res.json()
  } catch (_) {
    return { authenticated: false }
  }
}

async function enforceAuthMode() {
  const mode = getAuthMode()
  if (mode === "any") {
    return
  }

  const sessionData = await fetchSessionState()
  window.__authSession = sessionData
  document.dispatchEvent(new CustomEvent("auth-session-ready", { detail: sessionData }))

  if (mode === "public-only") {
    if (sessionData.authenticated) {
      const target = authRedirectTarget(sessionData)
      if (window.location.pathname !== target) {
        window.location.replace(target)
      }
    }
    return
  }

  if (mode === "protected") {
    if (!sessionData.authenticated) {
      window.location.replace("/login")
    }
    return
  }

  if (mode === "password-change-only") {
    if (!sessionData.authenticated) {
      window.location.replace("/login")
      return
    }
    if (!sessionData.force_password_change) {
      window.location.replace("/chat")
    }
  }
}

window.addEventListener("pageshow", () => {
  enforceAuthMode()
})

document.addEventListener("DOMContentLoaded", () => {
  enforceAuthMode()
})

document.addEventListener("auth-session-ready", (event) => {
  const data = event.detail || {}
  const sessionUserDisplay = document.getElementById("sessionUserDisplay")
  if (sessionUserDisplay && data.authenticated) {
    const role = data.role ? ` (${data.role})` : ""
    sessionUserDisplay.textContent = `${data.username || "user"}${role}`
  }
})

const loginForm = document.getElementById("loginForm")
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const fd = new FormData(loginForm)
    const username = String(fd.get("username") || "").trim()
    const password = String(fd.get("password") || "")
    const msg = document.getElementById("loginMsg")
    try {
      await requestJSON("/api/auth/login", "POST", { username, password })
      window.location.href = "/chat"
      return
    } catch (err) {
      msg.textContent = err.message || "Login failed"
      msg.className = "mt-3 text-sm text-red-600"
    }
  })
}

const logoutBtn = document.getElementById("logoutBtn")
if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    await requestJSON("/api/auth/logout", "POST", {})
    window.location.replace("/")
  })
}

const uploadForm = document.getElementById("uploadForm")
if (uploadForm) {
  let indexPath = ""
  const indexBtn = document.getElementById("indexBtn")

  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const msg = document.getElementById("uploadMsg")
    const fd = new FormData(uploadForm)
    const res = await fetch("/api/upload", { method: "POST", body: fd })
    const data = await res.json()
    if (data.ok) {
      msg.textContent = `Uploaded. Document ID: ${data.document_id} (${data.status})`
      msg.className = "mt-3 text-sm text-emerald-700"
      indexPath = data.index_path || ""
      if (indexBtn && indexPath) indexBtn.classList.remove("hidden")
      return
    }
    msg.textContent = data.error || "Upload failed"
    msg.className = "mt-3 text-sm text-red-600"
  })

  if (indexBtn) {
    indexBtn.addEventListener("click", async () => {
      const msg = document.getElementById("uploadMsg")
      if (!indexPath) return
      msg.textContent = "Indexing in progress..."
      msg.className = "mt-3 text-sm text-slate-700"

      const r = await fetch(indexPath, { method: "POST" })
      const data = await r.json()
      if (data.ok) {
        msg.textContent = `Indexed successfully. Chunks: ${data.chunks}`
        msg.className = "mt-3 text-sm text-emerald-700"
        return
      }
      msg.textContent = data.error || "Indexing failed"
      msg.className = "mt-3 text-sm text-red-600"
    })
  }
}

const refresh = document.getElementById("refreshMetrics")
if (refresh) {
  refresh.addEventListener("click", async () => {
    const box = document.getElementById("metricsBox")
    try {
      const data = await requestJSON("/api/admin/metrics")
      box.textContent = JSON.stringify(data, null, 2)
    } catch (err) {
      box.textContent = err.message
    }
  })

  refresh.click()
}

const accessRequestForm = document.getElementById("accessRequestForm")
if (accessRequestForm) {
  accessRequestForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const msg = document.getElementById("accessRequestMsg")
    const fd = new FormData(accessRequestForm)
    const payload = {
      full_name: String(fd.get("full_name") || "").trim(),
      email: String(fd.get("email") || "").trim(),
      organization: String(fd.get("organization") || "").trim(),
      use_case: String(fd.get("use_case") || "").trim(),
    }
    try {
      const data = await requestJSON("/api/auth/access-requests", "POST", payload)
      msg.textContent = data.message || "Request submitted"
      msg.className = "mt-3 text-sm text-emerald-700"
      accessRequestForm.reset()
      return
    } catch (err) {
      msg.textContent = err.message || "Request failed"
      msg.className = "mt-3 text-sm text-red-600"
    }
  })
}

const refreshUsers = document.getElementById("refreshUsers")
if (refreshUsers) {
  refreshUsers.addEventListener("click", async () => {
    const usersBox = document.getElementById("usersBox")
    try {
      const data = await requestJSON("/api/admin/users")
      usersBox.textContent = JSON.stringify(data, null, 2)
    } catch (err) {
      usersBox.textContent = err.message
    }
  })

  refreshUsers.click()
}

const adminResetUserPasswordForm = document.getElementById("adminResetUserPasswordForm")
if (adminResetUserPasswordForm) {
  adminResetUserPasswordForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const fd = new FormData(adminResetUserPasswordForm)
    const payload = { username: String(fd.get("username") || "").trim() }
    const msg = document.getElementById("adminResetUserPasswordMsg")
    const issuedCredentialBox = document.getElementById("issuedCredentialBox")
    try {
      const data = await requestJSON("/api/admin/users/reset-password", "POST", payload)
      issuedCredentialBox.textContent = JSON.stringify(data.credential || {}, null, 2)
      msg.textContent = `Temporary password generated for ${data.credential?.username || payload.username}`
      msg.className = "mt-2 text-sm text-emerald-700"
      adminResetUserPasswordForm.reset()
      document.getElementById("refreshUsers")?.click()
    } catch (err) {
      msg.textContent = err.message || "Unable to reset user password"
      msg.className = "mt-2 text-sm text-red-600"
    }
  })
}

async function approveRequest(requestId) {
  const usernameInput = document.getElementById(`approveUsername_${requestId}`)
  const roleInput = document.getElementById(`approveRole_${requestId}`)
  const notesInput = document.getElementById(`approveNotes_${requestId}`)
  const payload = {
    username: String(usernameInput?.value || "").trim(),
    role: String(roleInput?.value || "user"),
    notes: String(notesInput?.value || "").trim(),
  }

  const data = await requestJSON(`/api/admin/access-requests/${requestId}/approve`, "POST", payload)
  const issuedCredentialBox = document.getElementById("issuedCredentialBox")
  if (issuedCredentialBox) {
    issuedCredentialBox.textContent = JSON.stringify(data.credential || {}, null, 2)
  }
}

async function rejectRequest(requestId) {
  const notesInput = document.getElementById(`approveNotes_${requestId}`)
  const payload = { notes: String(notesInput?.value || "").trim() }
  return requestJSON(`/api/admin/access-requests/${requestId}/reject`, "POST", payload)
}

function renderAccessRequests(requests) {
  const list = document.getElementById("accessRequestsList")
  if (!list) return

  if (!requests.length) {
    list.innerHTML = "<p class=\"text-sm text-slate-600\">No pending requests.</p>"
    return
  }

  list.innerHTML = requests
    .map((req) => {
      const org = req.organization ? `<span>${req.organization}</span>` : ""
      const useCase = req.use_case ? req.use_case : "No use-case details submitted"
      return `
      <article class="border border-slate-200 rounded-xl p-4 bg-slate-50">
        <div class="flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-900">${req.full_name}</h3>
          <span class="text-xs uppercase tracking-wide px-2 py-1 rounded bg-amber-100 text-amber-800">${req.status}</span>
        </div>
        <p class="text-sm text-slate-700 mt-1">${req.email} ${org ? `• ${org}` : ""}</p>
        <p class="text-sm text-slate-700 mt-2">${useCase}</p>
        <div class="mt-3 grid md:grid-cols-3 gap-2">
          <input id="approveUsername_${req.id}" placeholder="Username (optional auto-generate)" class="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
          <select id="approveRole_${req.id}" class="border border-slate-300 rounded-lg px-3 py-2 text-sm">
            <option value="user">Service User</option>
            <option value="admin">Admin</option>
          </select>
          <input id="approveNotes_${req.id}" placeholder="Decision notes" class="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div class="mt-3 flex items-center gap-2">
          <button data-approve="${req.id}" class="px-3 py-2 rounded-lg bg-slate-900 text-white text-sm">Approve & Issue Credential</button>
          <button data-reject="${req.id}" class="px-3 py-2 rounded-lg border border-slate-300 text-sm">Reject</button>
        </div>
      </article>`
    })
    .join("")

  list.querySelectorAll("[data-approve]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const requestId = btn.getAttribute("data-approve")
      const msg = document.getElementById("accessRequestsMsg")
      try {
        await approveRequest(requestId)
        msg.textContent = `Request #${requestId} approved and credentials issued.`
        msg.className = "mt-3 text-sm text-emerald-700"
        document.getElementById("refreshAccessRequests")?.click()
        document.getElementById("refreshUsers")?.click()
      } catch (err) {
        msg.textContent = err.message
        msg.className = "mt-3 text-sm text-red-600"
      }
    })
  })

  list.querySelectorAll("[data-reject]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const requestId = btn.getAttribute("data-reject")
      const msg = document.getElementById("accessRequestsMsg")
      try {
        const data = await rejectRequest(requestId)
        msg.textContent = `Request #${requestId} rejected.`
        msg.className = "mt-3 text-sm text-emerald-700"
        document.getElementById("refreshAccessRequests")?.click()
      } catch (err) {
        msg.textContent = err.message
        msg.className = "mt-3 text-sm text-red-600"
      }
    })
  })
}

const refreshAccessRequests = document.getElementById("refreshAccessRequests")
if (refreshAccessRequests) {
  refreshAccessRequests.addEventListener("click", async () => {
    const msg = document.getElementById("accessRequestsMsg")
    try {
      const data = await requestJSON("/api/admin/access-requests?status=pending")
      renderAccessRequests(data.requests || [])
      msg.textContent = ""
    } catch (err) {
      msg.textContent = err.message
      msg.className = "mt-3 text-sm text-red-600"
    }
  })

  refreshAccessRequests.click()
}

const refreshAuthAudit = document.getElementById("refreshAuthAudit")
if (refreshAuthAudit) {
  refreshAuthAudit.addEventListener("click", async () => {
    const box = document.getElementById("authAuditBox")
    try {
      const data = await requestJSON("/api/admin/auth-audit")
      box.textContent = JSON.stringify(data, null, 2)
    } catch (err) {
      box.textContent = err.message || "Unable to load auth audit"
    }
  })

  refreshAuthAudit.click()
}

const passwordChangeForm = document.getElementById("passwordChangeForm")
if (passwordChangeForm) {
  passwordChangeForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const fd = new FormData(passwordChangeForm)
    const payload = {
      current_password: String(fd.get("current_password") || ""),
      new_password: String(fd.get("new_password") || ""),
    }
    const msg = document.getElementById("passwordChangeMsg")

    try {
      await requestJSON("/api/auth/change-password", "POST", payload)
      msg.textContent = "Password updated successfully. Redirecting..."
      msg.className = "mt-3 text-sm text-emerald-700"
      setTimeout(() => {
        window.location.href = "/chat"
      }, 400)
    } catch (err) {
      msg.textContent = err.message || "Unable to update password"
      msg.className = "mt-3 text-sm text-red-600"
    }
  })
}

const forgotPasswordForm = document.getElementById("forgotPasswordForm")
if (forgotPasswordForm) {
  forgotPasswordForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const fd = new FormData(forgotPasswordForm)
    const payload = {
      username_or_email: String(fd.get("username_or_email") || "").trim(),
    }
    const msg = document.getElementById("forgotPasswordMsg")
    const credentialBox = document.getElementById("forgotPasswordCredentialBox")
    try {
      const data = await requestJSON("/api/auth/forgot-password", "POST", payload)
      msg.textContent = data.message || "Temporary password generated."
      msg.className = "mt-3 text-sm text-emerald-700"
      if (credentialBox) {
        credentialBox.textContent = JSON.stringify(data.credential || {}, null, 2)
      }
      forgotPasswordForm.reset()
    } catch (err) {
      msg.textContent = err.message || "Unable to process request"
      msg.className = "mt-3 text-sm text-red-600"
      if (credentialBox) {
        credentialBox.textContent = ""
      }
    }
  })
}

const resetPasswordForm = document.getElementById("resetPasswordForm")
if (resetPasswordForm) {
  const tokenInput = document.getElementById("resetTokenInput")
  const params = new URLSearchParams(window.location.search)
  const tokenFromUrl = params.get("token") || ""
  if (tokenInput && tokenFromUrl) {
    tokenInput.value = tokenFromUrl
  }

  resetPasswordForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const fd = new FormData(resetPasswordForm)
    const payload = {
      token: String(fd.get("token") || "").trim(),
      new_password: String(fd.get("new_password") || ""),
    }
    const msg = document.getElementById("resetPasswordMsg")
    try {
      await requestJSON("/api/auth/reset-password", "POST", payload)
      msg.textContent = "Password reset successful. Redirecting to login..."
      msg.className = "mt-3 text-sm text-emerald-700"
      setTimeout(() => {
        window.location.href = "/login"
      }, 600)
    } catch (err) {
      msg.textContent = err.message || "Unable to reset password"
      msg.className = "mt-3 text-sm text-red-600"
    }
  })
}
