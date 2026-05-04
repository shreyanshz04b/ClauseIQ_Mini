let currentMode = 'english'

const modeButtons = document.querySelectorAll('.mode-btn')
const inputTextarea = document.getElementById('translationInput')
const outputDiv = document.getElementById('translationOutput')
const translateBtn = document.getElementById('translateBtn')
const clearBtn = document.getElementById('clearBtn')
const copyBtn = document.getElementById('copyBtn')
const downloadBtn = document.getElementById('downloadBtn')
const charCount = document.getElementById('charCount')
const inputLabel = document.getElementById('inputLabel')
const outputLabel = document.getElementById('outputLabel')
const inputStatus = document.getElementById('inputStatus')
const outputStatus = document.getElementById('outputStatus')
const glossarySearch = document.getElementById('glossarySearch')
const glossaryList = document.getElementById('glossaryList')
const statusMessage = document.getElementById('statusMessage')

modeButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    modeButtons.forEach(b => {
      b.classList.remove('mode-active')
      b.classList.add('border-slate-600', 'bg-slate-800/50', 'text-slate-300')
      b.classList.remove('border-amber-500', 'bg-amber-500/20', 'text-amber-300')
    })
    btn.classList.add('mode-active')
    btn.classList.remove('border-slate-600', 'bg-slate-800/50', 'text-slate-300')
    btn.classList.add('border-amber-500', 'bg-amber-500/20', 'text-amber-300')
    
    currentMode = btn.getAttribute('data-mode')
    if (currentMode === 'english') {
      inputLabel.textContent = 'English Legal Text'
      outputLabel.textContent = 'Hindi Translation (Technical & Simplified)'
    } else {
      inputLabel.textContent = 'Hindi Legal Text'
      outputLabel.textContent = 'English Translation'
    }
    inputTextarea.placeholder = currentMode === 'english' ? 
      'Paste your English legal text here...' : 
      'Paste your Hindi legal text here...'
    inputTextarea.value = ''
    outputDiv.innerHTML = '<p class="text-slate-500 text-center mt-24">Translation will appear here...</p>'
    copyBtn.disabled = true
    downloadBtn.disabled = true
    charCount.textContent = '0'
  })
})

inputTextarea.addEventListener('input', () => {
  charCount.textContent = inputTextarea.value.length
})

clearBtn.addEventListener('click', () => {
  inputTextarea.value = ''
  outputDiv.innerHTML = '<p class="text-slate-500 text-center mt-24">Translation will appear here...</p>'
  copyBtn.disabled = true
  downloadBtn.disabled = true
  charCount.textContent = '0'
  inputStatus.textContent = ''
})

translateBtn.addEventListener('click', async () => {
  const text = inputTextarea.value.trim()
  
  if (!text) {
    showStatus('Please enter text to translate', 'error')
    return
  }
  
  if (text.length < 3) {
    showStatus('Text must be at least 3 characters', 'error')
    return
  }
  
  if (text.length > 5000) {
    showStatus('Text exceeds 5000 character limit', 'error')
    return
  }
  
  translateBtn.disabled = true
  translateBtn.textContent = 'Translating...'
  outputStatus.textContent = 'Processing...'
  
  try {
    const endpoint = currentMode === 'english' ? '/api/translate/to-hindi' : '/api/translate/to-english'
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate'
      },
      body: JSON.stringify({ text })
    })
    
    const data = await res.json()
    
    if (!res.ok) {
      showStatus(data.error || 'Translation failed', 'error')
      outputDiv.innerHTML = '<p class="text-red-400 text-center mt-24">Error: ' + (data.error || 'Translation failed') + '</p>'
    } else {
      outputDiv.innerHTML = `<div class="prose prose-invert max-w-none"><pre class="bg-slate-900/50 p-4 rounded border border-white/10 whitespace-pre-wrap break-words text-sm">${escapeHTML(data.translation)}</pre></div>`
      copyBtn.disabled = false
      downloadBtn.disabled = false
      showStatus('Translation complete', 'success')
      outputStatus.textContent = ''
    }
  } catch (err) {
    showStatus('Connection error: ' + err.message, 'error')
    outputDiv.innerHTML = '<p class="text-red-400 text-center mt-24">Error: Connection failed</p>'
  } finally {
    translateBtn.disabled = false
    translateBtn.textContent = 'Translate'
  }
})

copyBtn.addEventListener('click', () => {
  const text = outputDiv.innerText
  navigator.clipboard.writeText(text).then(() => {
    showStatus('Translation copied to clipboard', 'success')
  }).catch(() => {
    showStatus('Failed to copy translation', 'error')
  })
})

downloadBtn.addEventListener('click', () => {
  const text = outputDiv.innerText
  const element = document.createElement('a')
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text))
  element.setAttribute('download', `translation_${Date.now()}.txt`)
  element.style.display = 'none'
  document.body.appendChild(element)
  element.click()
  document.body.removeChild(element)
  showStatus('Translation downloaded', 'success')
})

glossarySearch.addEventListener('input', async (e) => {
  const searchTerm = e.target.value.trim()
  
  if (!searchTerm) {
    glossaryList.innerHTML = '<p class="text-slate-500 text-sm">Enter a term to search...</p>'
    return
  }
  
  try {
    const res = await fetch(`/api/glossary?search=${encodeURIComponent(searchTerm)}`)
    const data = await res.json()
    
    if (data.glossary && data.glossary.length > 0) {
      glossaryList.innerHTML = data.glossary.map(item => `
        <div class="border-l-2 border-amber-500 pl-3 py-2">
          <div class="text-sm font-semibold text-amber-300">${escapeHTML(item.english)}</div>
          <div class="text-sm text-slate-300">${escapeHTML(item.hindi)}</div>
        </div>
      `).join('')
    } else {
      glossaryList.innerHTML = '<p class="text-slate-500 text-sm">No matching terms found</p>'
    }
  } catch (err) {
    glossaryList.innerHTML = '<p class="text-red-400 text-sm">Error loading glossary</p>'
  }
})

function escapeHTML(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function showStatus(message, type) {
  statusMessage.textContent = message
  statusMessage.className = `fixed bottom-6 right-6 px-6 py-3 rounded-lg border border-white/15 text-white max-w-sm ${
    type === 'error' ? 'bg-red-900/90 border-red-500/30' : 'bg-green-900/90 border-green-500/30'
  }`
  statusMessage.classList.remove('hidden')
  
  setTimeout(() => {
    statusMessage.classList.add('hidden')
  }, 4000)
}

// Load initial glossary
window.addEventListener('load', async () => {
  try {
    const res = await fetch('/api/glossary')
    const data = await res.json()
    if (data.glossary && data.glossary.length > 0) {
      glossaryList.innerHTML = `<p class="text-slate-400 text-xs mb-3">${data.total} legal terms available</p>` + 
        data.glossary.slice(0, 5).map(item => `
          <div class="border-l-2 border-amber-500 pl-3 py-2">
            <div class="text-sm font-semibold text-amber-300">${escapeHTML(item.english)}</div>
            <div class="text-sm text-slate-300">${escapeHTML(item.hindi)}</div>
          </div>
        `).join('')
    }
  } catch (err) {
    console.error('Error loading glossary:', err)
  }
})
