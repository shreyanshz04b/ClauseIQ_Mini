const chatForm = document.getElementById("chatForm")
const chatBox = document.getElementById("chatBox")
const chatStatus = document.getElementById("chatStatus")
const uploadTrigger = document.getElementById("uploadTrigger")
const chatFileInput = document.getElementById("chatFileInput")
const docsList = document.getElementById("docsList")
const refreshDocs = document.getElementById("refreshDocs")
const chatInput = chatForm?.querySelector('input[name="query"]')
const chatSubmitBtn = chatForm?.querySelector('button[type="submit"]')

function escapeHTML(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
}

function addLine(who, text, isCitation) {
  if (isCitation === undefined) {
    isCitation = false
  }
  const div = document.createElement("div")
  const isUser = who === "You"
  let className = "chat-bubble"
  if (isUser) {
    className = className + " user"
  }
  div.className = className
  
  const safeText = escapeHTML(text).replaceAll("\n", "<br>")
  let contentClass = "chat-bubble-content"
  if (isUser) {
    contentClass = contentClass + " user"
  } else {
    contentClass = contentClass + " assistant"
  }
  
  div.innerHTML = `
    <div class="${contentClass}">
      <p class="chat-bubble-label">${escapeHTML(who)}</p>
      <p class="chat-bubble-text">${safeText}</p>
    </div>
  `
  chatBox.appendChild(div)
  chatBox.scrollTop = chatBox.scrollHeight
  
  if (isUser) {
    announceToScreenReader(`You said: ${text}`)
  } else if (isCitation) {
    announceToScreenReader(`Citations: ${text}`)
  } else {
    announceToScreenReader(`Assistant: ${text}`)
  }
}

function announceToScreenReader(message) {
  const announcement = document.createElement("div")
  announcement.className = "sr-only"
  announcement.setAttribute("role", "status")
  announcement.setAttribute("aria-live", "polite")
  announcement.textContent = message
  document.body.appendChild(announcement)
  setTimeout(() => announcement.remove(), 1000)
}

function setStatus(message, isError) {
  if (isError === undefined) {
    isError = false
  }
  if (!chatStatus) return
  chatStatus.textContent = message
  if (isError) {
    chatStatus.className = "mt-2 text-xs text-red-600"
  } else {
    chatStatus.className = "mt-2 text-xs text-slate-500"
  }
  
  if (message) {
    announceToScreenReader(message)
  }
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return "-"
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function loadDocuments() {
  if (!docsList) return
  const res = await fetch("/api/documents")
  const data = await res.json()
  if (!data.ok) {
    docsList.innerHTML = '<p class="text-xs text-red-600">Failed to load documents.</p>'
    return
  }

  if (!data.documents.length) {
    docsList.innerHTML = '<p class="text-xs text-slate-500">No documents uploaded yet.</p>'
    return
  }

  let html = ""
  for (let i = 0; i < data.documents.length; i++) {
    const doc = data.documents[i]
    let statusClass = "pending"
    if (doc.status === "indexed") {
      statusClass = "indexed"
    } else if (doc.status === "rejected_non_legal") {
      statusClass = "rejected"
    }

    const docHtml = `
        <div class="doc-card">
          <p class="doc-card-title" title="${escapeHTML(doc.name)}">${escapeHTML(doc.name)}</p>
          <p class="doc-card-status ${statusClass}">Status: ${escapeHTML(doc.status)}</p>
          <p class="text-[11px] text-slate-500">${formatBytes(doc.size)}</p>
          <button data-doc-delete="${doc.id}" class="doc-card-delete">Delete</button>
        </div>
      `
    html = html + docHtml
  }
  docsList.innerHTML = html
}

async function deleteDocument(documentId) {
  const res = await fetch(`/api/documents/${documentId}`, { method: "DELETE" })
  const data = await res.json()
  if (!data.ok) {
    setStatus(data.error || "Delete failed", true)
    return
  }
  setStatus("Document deleted")
  await loadDocuments()
}

async function uploadAndIndex(file) {
  const fd = new FormData()
  fd.append("file", file)

  setStatus("Uploading document...")
  const uploadRes = await fetch("/api/upload", { 
    method: "POST", 
    body: fd,
    headers: {
      "Cache-Control": "no-cache, no-store, must-revalidate",
      "Pragma": "no-cache"
    }
  })
  const uploadData = await uploadRes.json()
  if (!uploadData.ok) {
    const errorMsg = uploadData.error || "Upload failed"
    setStatus(errorMsg, true)
    addLine("Assistant", errorMsg)
    return
  }

  setStatus(uploadData.message || "Document uploaded and indexed")
  await loadDocuments()
}

if (uploadTrigger && chatFileInput) {
  uploadTrigger.addEventListener("click", () => chatFileInput.click())
  chatFileInput.addEventListener("change", async () => {
    const selected = chatFileInput.files && chatFileInput.files[0]
    if (!selected) return
    await uploadAndIndex(selected)
    chatFileInput.value = ""
  })
}

if (refreshDocs) {
  refreshDocs.addEventListener("click", () => {
    loadDocuments()
  })
}

if (docsList) {
  docsList.addEventListener("click", async (e) => {
    const target = e.target
    if (!(target instanceof HTMLElement)) return
    const id = target.getAttribute("data-doc-delete")
    if (!id) return
    await deleteDocument(id)
  })
}

// Keyboard shortcuts
if (chatInput) {
  chatInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault()
      chatForm.dispatchEvent(new Event("submit"))
    }
    if (e.key === "Escape") {
      e.preventDefault()
      chatInput.value = ""
      chatInput.focus()
    }
  })
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault()
  const fd = new FormData(chatForm)
  const query = String(fd.get("query") || "").trim()
  
  if (!query) return
  
  if (!/[a-zA-Z0-9]/.test(query)) {
    setStatus("Please enter a valid question with meaningful content", true)
    return
  }
  
  const words = query.split(/\s+/)
  if (words.length < 2 && query.length < 5) {
    setStatus("Please provide a more detailed question", true)
    return
  }

  if (chatSubmitBtn) chatSubmitBtn.disabled = true

  addLine("You", query)
  chatForm.reset()
  setStatus("Thinking...")

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache"
      },
      body: JSON.stringify({ query }),
    })
    const data = await res.json()
    
    if (data.error) {
      setStatus(data.error, true)
      addLine("Assistant", data.error)
      if (data.citations && data.citations.length > 0) {
        let citationText = ""
        for (let i = 0; i < data.citations.length; i++) {
          const citation = data.citations[i]
          if (citationText !== "") citationText += "\n\n"
          citationText += `[Source ${i + 1}] ${citation}`
        }
        addLine("Citations", citationText, true)
      }
    } else if (res.status >= 400) {
      setStatus(data.response, true)
      addLine("Assistant", data.response)
      if (data.citations && data.citations.length > 0) {
        let citationText = ""
        for (let i = 0; i < data.citations.length; i++) {
          const citation = data.citations[i]
          if (citationText !== "") citationText += "\n\n"
          citationText += `[Source ${i + 1}] ${citation}`
        }
        addLine("Citations", citationText, true)
      }
    } else {
      addLine("Assistant", data.response || "No response")
      setStatus("")

      if (data.citations && data.citations.length > 0) {
        let citationText = ""
        for (let i = 0; i < data.citations.length; i++) {
          const citation = data.citations[i]
          if (citationText !== "") citationText += "\n\n"
          citationText += `[Source ${i + 1}] ${citation}`
        }
        addLine("Citations", citationText, true)
      }
    }
  } catch (err) {
    setStatus("Connection error. Please try again.", true)
    addLine("Assistant", "Failed to get response. Please check your connection.")
  } finally {
    if (chatSubmitBtn) chatSubmitBtn.disabled = false
    if (chatInput) chatInput.focus()
  }
})

loadDocuments()

let hasStyle = false
const styles = document.querySelectorAll("style")
for (let i = 0; i < styles.length; i++) {
  if (styles[i].textContent.includes("sr-only")) {
    hasStyle = true
    break
  }
}
if (!hasStyle) {
  const style = document.createElement("style")
  style.textContent = `
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    }
  `
  document.head.appendChild(style)
}
