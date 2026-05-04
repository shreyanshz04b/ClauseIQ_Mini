/**
 * Legal Sections Explorer - Frontend Logic
 */

let currentResults = [];
let currentDetailSection = null;
let currentExplanation = null;
let selectedAct = null;
const explanationCache = {};

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const resultsContainer = document.getElementById('resultsContainer');
const resultCount = document.getElementById('resultCount');
const loadingSpinner = document.getElementById('loadingSpinner');
const detailModal = document.getElementById('detailModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const actFilterContainer = document.getElementById('actFilterContainer');
const clearFiltersBtn = document.getElementById('clearFiltersBtn');
const toastContainer = document.getElementById('toastContainer');
const explanationTabs = document.querySelectorAll('.explanation-tab');
const explanationContent = document.getElementById('explanationContent');
const copyExplanationBtn = document.getElementById('copyExplanationBtn');
const shareBtn = document.getElementById('shareBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadLegalActs();
  setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
  searchBtn.addEventListener('click', performSearch);
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
  });
  closeModalBtn.addEventListener('click', closeDetailModal);
  detailModal.addEventListener('click', (e) => {
    if (e.target === detailModal) closeDetailModal();
  });
  clearFiltersBtn.addEventListener('click', clearFilters);
  copyExplanationBtn.addEventListener('click', copyExplanation);
  shareBtn.addEventListener('click', shareSection);

  // Explanation tabs
  explanationTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const style = tab.dataset.style;
      loadExplanation(style);
    });
  });
}

// Load Legal Acts
async function loadLegalActs() {
  try {
    const response = await fetch('/api/explorer/acts');
    const data = await response.json();

    if (data.ok) {
      const acts = data.acts;
      actFilterContainer.innerHTML = '';

      acts.forEach(act => {
        const label = document.createElement('label');
        label.className = 'flex items-center gap-2 cursor-pointer hover:opacity-80 transition';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = act;
        checkbox.className = 'w-4 h-4 rounded border-slate-500 bg-slate-700 accent-amber-500';
        checkbox.addEventListener('change', () => {
          selectedAct = checkbox.checked ? act : null;
          performSearch();
        });

        const span = document.createElement('span');
        span.className = 'text-slate-300 text-sm';
        span.textContent = `${act} (${data.statistics.acts[act]})`;

        label.appendChild(checkbox);
        label.appendChild(span);
        actFilterContainer.appendChild(label);
      });
    }
  } catch (error) {
    console.error('Error loading acts:', error);
    showToast('Failed to load legal acts', 'error');
  }
}

// Perform Search
async function performSearch() {
  const query = searchInput.value.trim();

  if (!query || query.length < 2) {
    showToast('Please enter at least 2 characters', 'warning');
    return;
  }

  showSpinner(true);

  try {
    let url = `/api/explorer/search?query=${encodeURIComponent(query)}&limit=20`;
    if (selectedAct) {
      url += `&act=${encodeURIComponent(selectedAct)}`;
    }

    const response = await fetch(url);
    const data = await response.json();

    showSpinner(false);

    if (data.ok) {
      currentResults = data.results;
      displayResults(data.results);
      resultCount.textContent = data.count;
      showToast(`Found ${data.count} results`, 'success');
    } else {
      showToast(data.error || 'Search failed', 'error');
    }
  } catch (error) {
    console.error('Search error:', error);
    showSpinner(false);
    showToast('Failed to perform search', 'error');
  }
}

// Display Results
function displayResults(results) {
  resultsContainer.innerHTML = '';

  if (results.length === 0) {
    resultsContainer.innerHTML = `
      <div class="col-span-full border border-white/15 rounded-lg bg-slate-800/30 p-8 text-center">
        <p class="text-slate-400">No results found. Try a different search term.</p>
      </div>
    `;
    return;
  }

  results.forEach(section => {
    const card = createSectionCard(section);
    resultsContainer.appendChild(card);
  });
}

// Create Section Card
function createSectionCard(section) {
  const card = document.createElement('div');
  card.className = 'section-card';

  const keywordBadges = section.keywords
    .slice(0, 2)
    .map(kw => `<span class="badge">${kw}</span>`)
    .join('');

  card.innerHTML = `
    <h3>${section.act_name}</h3>
    <div class="section-number">Section ${section.section_number}</div>
    <div class="section-title">${escapeHtml(section.title)}</div>
    <div class="section-desc">${escapeHtml(section.description.substring(0, 100))}...</div>
    <div class="section-meta">
      <span class="badge">${section.category}</span>
      ${keywordBadges}
    </div>
    <button class="btn-view">View Details</button>
  `;

  card.querySelector('.btn-view').addEventListener('click', () => {
    openDetailModal(section.id);
  });

  return card;
}

// Open Detail Modal
async function openDetailModal(sectionId) {
  showSpinner(true);

  try {
    const response = await fetch(`/api/explorer/section/${sectionId}`);
    const data = await response.json();

    showSpinner(false);

    if (data.ok) {
      currentDetailSection = data.section;
      populateDetailModal(data.section);
      detailModal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';

      // Load simple explanation by default
      loadExplanation('simple');
    } else {
      showToast(data.error || 'Failed to load section', 'error');
    }
  } catch (error) {
    console.error('Error loading section:', error);
    showSpinner(false);
    showToast('Failed to load section details', 'error');
  }
}

// Populate Detail Modal
function populateDetailModal(section) {
  document.getElementById('modalTitle').textContent = section.title;
  document.getElementById('modalMeta').textContent = `${section.act_name} • Section ${section.section_number}`;
  document.getElementById('modalSectionText').textContent = section.full_description;
  document.getElementById('modalCategory').textContent = section.category;

  // Keywords
  const keywordsDiv = document.getElementById('modalKeywords');
  keywordsDiv.innerHTML = section.keywords
    .map(kw => `<span class="inline-block px-3 py-1 bg-amber-500/20 text-amber-300 rounded-full text-sm">${kw}</span>`)
    .join('');

  // Reset tabs
  explanationTabs.forEach((tab, idx) => {
    if (idx === 0) {
      tab.classList.add('border-amber-500', 'text-amber-400');
      tab.classList.remove('border-transparent', 'text-slate-400');
    } else {
      tab.classList.add('border-transparent', 'text-slate-400');
      tab.classList.remove('border-amber-500', 'text-amber-400');
    }
  });
}

// Load Explanation
async function loadExplanation(style) {
  // Update active tab
  explanationTabs.forEach(tab => {
    if (tab.dataset.style === style) {
      tab.classList.add('border-amber-500', 'text-amber-400');
      tab.classList.remove('border-transparent', 'text-slate-400');
    } else {
      tab.classList.add('border-transparent', 'text-slate-400');
      tab.classList.remove('border-amber-500', 'text-amber-400');
    }
  });

  // Show loading
  explanationContent.innerHTML = `
    <div class="flex items-center gap-2 text-slate-400">
      <span class="animate-spin">⚙️</span>
      <span>Generating ${style} explanation...</span>
    </div>
  `;

  // Check cache
  const cacheKey = `${currentDetailSection.id}-${style}`;
  if (explanationCache[cacheKey]) {
    currentExplanation = explanationCache[cacheKey];
    explanationContent.innerHTML = escapeHtml(currentExplanation);
    return;
  }

  try {
    let endpoint = '/api/explorer/explain';
    let payload = {
      section_id: currentDetailSection.id,
      style: style
    };

    if (style === 'hindi') {
      endpoint = '/api/explorer/explain-hindi';
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (data.ok) {
      currentExplanation = data.explanation;
      explanationCache[cacheKey] = data.explanation;
      explanationContent.innerHTML = escapeHtml(data.explanation);
    } else {
      explanationContent.innerHTML = `<span class="text-red-400">${data.error || 'Failed to generate explanation'}</span>`;
    }
  } catch (error) {
    console.error('Error loading explanation:', error);
    explanationContent.innerHTML = '<span class="text-red-400">Failed to load explanation</span>';
  }
}

// Close Detail Modal
function closeDetailModal() {
  detailModal.classList.add('hidden');
  document.body.style.overflow = 'auto';
  currentDetailSection = null;
  currentExplanation = null;
}

// Clear Filters
function clearFilters() {
  selectedAct = null;
  document.querySelectorAll('#actFilterContainer input[type="checkbox"]').forEach(checkbox => {
    checkbox.checked = false;
  });
  showToast('Filters cleared', 'info');
}

// Copy Explanation
function copyExplanation() {
  if (currentExplanation) {
    navigator.clipboard.writeText(currentExplanation).then(() => {
      showToast('Explanation copied to clipboard', 'success');
    });
  }
}

// Share Section
function shareSection() {
  if (currentDetailSection) {
    const text = `${currentDetailSection.title}\n${currentDetailSection.act_name} - Section ${currentDetailSection.section_number}\n\n${currentExplanation}`;
    
    if (navigator.share) {
      navigator.share({
        title: currentDetailSection.title,
        text: text
      });
    } else {
      navigator.clipboard.writeText(text).then(() => {
        showToast('Section copied to clipboard for sharing', 'success');
      });
    }
  }
}

// Utility Functions
function showSpinner(show) {
  if (show) {
    loadingSpinner.classList.remove('hidden');
  } else {
    loadingSpinner.classList.add('hidden');
  }
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `px-6 py-3 rounded-lg font-medium text-sm transition transform animate-slide-in ${
    type === 'success' ? 'bg-green-500/90 text-white' :
    type === 'error' ? 'bg-red-500/90 text-white' :
    type === 'warning' ? 'bg-yellow-500/90 text-white' :
    'bg-blue-500/90 text-white'
  }`;
  toast.textContent = message;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
  @keyframes slide-in {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  .animate-slide-in {
    animation: slide-in 0.3s ease-out;
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`;
document.head.appendChild(style);
