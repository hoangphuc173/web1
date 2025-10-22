/**
 * Streaming page script (clean, modular)
 * Uses core modules: AppConfig, api, auth, notifications, smartStorage, Utils
 */

let currentUser = null;
let userFavorites = [];
let refreshInterval = null;

initializePage('Streaming', async () => {
    // Wait for the initial auth check to complete
    await auth.initPromise;

    // Listen for auth changes
    auth.onAuthStateChange(user => {
        currentUser = user;
        console.log('Auth state changed:', user ? user.email : 'No user');
        renderUserMenu();
        if (user) {
            loadUserData();
        } else {
            // Clear user-specific data if logged out
            const myListSection = document.getElementById('myListSectionBottom');
            if (myListSection) {
                myListSection.style.display = 'none';
            }
        }
    });

    // Initial render based on current state
    currentUser = auth.getCurrentUser();
    renderUserMenu();
    if (currentUser) {
        loadUserData();
    } else {
        const myListSection = document.getElementById('myListSectionBottom');
        if (myListSection) {
            myListSection.style.display = 'none';
        }
    }
    
    setupNavbar();
    setupSearch();
    loadMovies();
    loadGenres();
    // loadSidebarData(); // Disabled - sidebar removed
    loadHeroBanner();
    setupAutoRefresh();
});

function renderUserMenu() {
    const userNameEl = document.getElementById('userName');
    const userMenu = document.getElementById('userMenu');
    if (!userNameEl || !userMenu) return;

    if (currentUser) {
        userNameEl.textContent = currentUser.name || currentUser.email || 'Tài khoản';
        userMenu.onclick = null;
    } else {
        userNameEl.textContent = 'Đăng nhập';
        userMenu.onclick = () => window.location.href = '/login.html';
    }
}

function setupNavbar() {
    window.addEventListener('scroll', Utils.throttle(() => {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;
        if (window.scrollY > 100) navbar.classList.add('scrolled'); else navbar.classList.remove('scrolled');
    }, 100));
}

// Auto-refresh
function setupAutoRefresh() {
    const enabled = smartStorage.get('autoRefresh', AppConfig.features.autoRefresh);
    if (enabled) {
        refreshInterval = setInterval(refreshData, AppConfig.features.refreshInterval);
        logger.info('Auto-refresh enabled');
    }
}

function toggleAutoRefresh() {
    const current = smartStorage.get('autoRefresh', true);
    const next = !current;
    smartStorage.set('autoRefresh', next);
    if (next) {
        setupAutoRefresh();
        notifications.success('Đã bật tự động làm mới!', 'Cài đặt');
    } else {
        if (refreshInterval) { clearInterval(refreshInterval); refreshInterval = null; }
        notifications.info('Đã tắt tự động làm mới', 'Cài đặt');
    }
}

async function refreshData() {
    try {
        await loadMovies();
        // await loadSidebarData(); // Disabled - sidebar removed
        if (currentUser) await loadUserData();
        notifications.info('Đã cập nhật dữ liệu mới', 'Tự động làm mới');
    } catch (err) {
        logger.error('Error during refresh', err);
    }
}

// Load movies and render
async function loadMovies() {
    try {
        console.log('🎬 Loading movies...');
        
        // Load all movies in ONE request with larger limit
        // Sort by updated_at DESC from backend to get latest updates first
        const res = await api.get(AppConfig.api.endpoints.movies, { 
            per_page: 500,
            sort: 'updated_at',
            order: 'desc'
        });
        console.log('API Response:', res);
        
        if (res && res.success) {
            const all = res.data || [];
            console.log(`Total movies loaded: ${all.length}`);
            console.log('First 3 movies (should be newest by updated_at):');
            all.slice(0, 3).forEach((m, i) => {
                console.log(`  ${i+1}. ${m.title} - Updated: ${m.updated_at}`);
            });
            
            // Filter on client side instead of making multiple API calls
            const movies = all.filter(m => m.type === 'movie');
            const series = all.filter(m => m.type === 'series');
            
            // Trending: Sort by views (most viewed)
            const trending = [...all].sort((a, b) => (b.views || 0) - (a.views || 0));
            
            // Recommended: High rated movies (IMDb >= 7.0)
            const recommended = all.filter(m => parseFloat(m.imdb_rating || 0) >= 7.0)
                                   .sort((a, b) => (b.imdb_rating || 0) - (a.imdb_rating || 0));
            
            // Top Rated: Movies with rating >= 8.0
            const topRated = all.filter(m => parseFloat(m.imdb_rating || 0) >= 8.0)
                                .sort((a, b) => (b.imdb_rating || 0) - (a.imdb_rating || 0));
            
            // Helper function to check genre (support both TEXT field and array)
            const hasGenre = (movie, genreNames) => {
                const genresText = movie.genres || '';
                if (typeof genresText === 'string') {
                    const lowerText = genresText.toLowerCase();
                    return genreNames.some(name => lowerText.includes(name.toLowerCase()));
                }
                const genres = movie.category || [];
                if (!Array.isArray(genres)) return false;
                
                return genres.some(g => {
                    const genreName = (typeof g === 'string' ? g : g.name || '').toLowerCase();
                    return genreNames.some(name => genreName.includes(name.toLowerCase()));
                });
            };
            
            // Genre-based sections (updated to match Vietnamese names in database)
            const action = all.filter(m => hasGenre(m, ['hành động', 'hanh-dong']));
            const comedy = all.filter(m => hasGenre(m, ['hài hước', 'hai-huoc']));
            const drama = all.filter(m => hasGenre(m, ['tâm lý', 'tam-ly']));
            const horror = all.filter(m => hasGenre(m, ['kinh dị', 'kinh-di']));
            const romance = all.filter(m => hasGenre(m, ['tình cảm', 'tinh-cam']));
            const crime = all.filter(m => hasGenre(m, ['hình sự', 'hinh-su']));
            const scifi = all.filter(m => hasGenre(m, ['viễn tưởng', 'vien-tuong']));
            const fantasy = all.filter(m => hasGenre(m, ['thần thoại', 'than-thoai']));
            
            // New Releases - Already sorted by updated_at DESC from backend
            // Just take top 20 movies (no need to re-sort since backend already sorted)
            const newReleases = all.slice(0, 20);
            
            // Debug: Log new releases with updated_at times
            console.log('New Releases (top 20 from backend, sorted by updated_at DESC):');
            newReleases.slice(0, 5).forEach((m, i) => {
                console.log(`  ${i+1}. ${m.title} - Updated: ${m.updated_at}, Created: ${m.created_at}`);
            });
            
            console.log(`Movies: ${movies.length}, Series: ${series.length}, Trending: ${trending.length}, Recommended: ${recommended.length}`);
            console.log(`New Releases: ${newReleases.length}, Top Rated: ${topRated.length}, Action: ${action.length}, Comedy: ${comedy.length}, Drama: ${drama.length}, Horror: ${horror.length}`);
            console.log(`Romance: ${romance.length}, Crime: ${crime.length}, Sci-Fi: ${scifi.length}, Fantasy: ${fantasy.length}`);
            
            // Display all sections with limit (1 row = 8 items)
            displayMovies(trending, 'trendingMovies', 8);
            
            // New Releases section
            if (newReleases.length > 0) {
                displayMovies(newReleases, 'newReleases', 8);
            }

            // Movies (Phim lẻ) and Series (Phim bộ)
            if (movies.length > 0) {
                displayMovies(movies, 'movies', 8);
            }
            if (series.length > 0) {
                displayMovies(series, 'series', 8);
            }
            
            // Show recommended section only if user is logged in
            if (currentUser && recommended.length > 0) {
                displayMovies(recommended, 'recommendedMovies', 8);
                document.getElementById('recommendedSection').style.display = 'block';
            }
            
            // Display new sections
            if (topRated.length > 0) {
                displayMovies(topRated, 'topRatedMovies', 8);
            }
            
            if (action.length > 0) {
                displayMovies(action, 'actionMovies', 8);
            }
            
            if (comedy.length > 0) {
                displayMovies(comedy, 'comedyMovies', 8);
            }
            
            if (drama.length > 0) {
                displayMovies(drama, 'dramaMovies', 8);
            }
            
            if (horror.length > 0) {
                displayMovies(horror, 'horrorMovies', 8);
            }
            
            if (romance.length > 0) {
                displayMovies(romance, 'romanceMovies', 8);
            }
            
            if (crime.length > 0) {
                displayMovies(crime, 'crimeMovies', 8);
            }
            
            if (scifi.length > 0) {
                displayMovies(scifi, 'scifiMovies', 8);
            }
            
            if (fantasy.length > 0) {
                displayMovies(fantasy, 'fantasyMovies', 8);
            }
        }
        
        console.log('✅ Movies loaded successfully!');
    } catch (error) {
        console.error('❌ Error loading movies:', error);
        logger.error('loadMovies failed', error);
        notifications.error('Không thể tải danh sách phim. Vui lòng thử lại!', 'Lỗi');
    }
}

function buildMovieCard(item) {
    const card = document.createElement('div');
    card.className = 'movie-card';
    card.onclick = () => showMovieDetail(item.id || item.movie_id);

    const img = document.createElement('img');
    // Use lazy loading for better performance
    img.loading = 'lazy';
    
    // Use poster URL or placeholder
    let posterUrl = item.poster_url;
    
    // Improve image quality if using ophim CDN
    if (posterUrl && (posterUrl.includes('ophim') || posterUrl.includes('_next/image'))) {
        // Request higher quality image (width: 500px, quality: 90)
        posterUrl = posterUrl.replace(/&w=\d+/g, '&w=500').replace(/&q=\d+/g, '&q=90');
    }
    
    img.src = posterUrl || 'https://via.placeholder.com/200x300?text=No+Image';
    img.alt = item.title || 'No title';
    
    // Fallback: Try proxy if direct load fails
    img.onerror = function() {
        if (posterUrl && !this.src.includes('/api/image-proxy')) {
            // Try loading through proxy
            this.src = `/api/image-proxy?url=${encodeURIComponent(posterUrl)}`;
            this.onerror = function() {
                // Final fallback
                this.src = 'https://via.placeholder.com/200x300?text=No+Image';
                this.onerror = null;
            };
        } else {
            this.src = 'https://via.placeholder.com/200x300?text=No+Image';
            this.onerror = null;
        }
    };

    // Add quality badge (top-left corner)
    const qualityBadge = document.createElement('div');
    qualityBadge.className = 'movie-card-quality';
    qualityBadge.textContent = item.quality || 'HD';
    card.appendChild(qualityBadge);

    // Add status badge (top-right corner) - Only for series and only when meaningful
    if (item.type === 'series') {
        const statusBadge = document.createElement('div');
        statusBadge.className = 'movie-card-status';
        const epText = (item.episode_current || '').toString();
        const epLower = epText.toLowerCase();
        let showBadge = false;
        if (epLower.includes('full')) {
            statusBadge.textContent = 'FULL';
            statusBadge.classList.add('full');
            showBadge = true;
        } else if (epText) {
            // Only show when episode number > 1, hide "Tập 1" or equivalents
            const match = epText.match(/\d+/);
            if (match && parseInt(match[0], 10) > 1) {
                statusBadge.textContent = epText;
                showBadge = true;
            }
        }
        if (showBadge) {
            card.appendChild(statusBadge);
        }
    }
    // For movies (phim lẻ), don't show episode badge at all

    const overlay = document.createElement('div');
    overlay.className = 'movie-card-overlay';

    const title = document.createElement('div');
    title.className = 'movie-card-title';
    title.textContent = item.title || '';

    const meta = document.createElement('div');
    meta.className = 'movie-card-meta';
    
    // IMDb rating with star icon
    const ratingSpan = document.createElement('span');
    ratingSpan.className = 'movie-card-rating';
    ratingSpan.innerHTML = `<i class="fas fa-star"></i> ${item.imdb_rating || 'N/A'}`;
    
    // Year
    const yearSpan = document.createElement('span');
    yearSpan.className = 'movie-card-year';
    yearSpan.textContent = item.release_year || '';
    
    meta.appendChild(ratingSpan);
    meta.appendChild(yearSpan);

    // Build overlay structure: title -> meta -> genres (hidden by default, shown on hover)
    overlay.appendChild(title);
    overlay.appendChild(meta);
    
    // Genre tags (show first 2 genres) - will appear on hover
    if (item.genres && Array.isArray(item.genres) && item.genres.length > 0) {
        const genreContainer = document.createElement('div');
        genreContainer.className = 'movie-card-genres';
        
        const genresToShow = item.genres.slice(0, 2);
        genresToShow.forEach(genre => {
            const genreTag = document.createElement('span');
            genreTag.className = 'genre-tag';
            genreTag.textContent = genre.name || genre;
            genreContainer.appendChild(genreTag);
        });
        
        overlay.appendChild(genreContainer);
    }
    
    // Add play icon overlay
    const playIcon = document.createElement('div');
    playIcon.className = 'movie-card-play-icon';
    playIcon.innerHTML = '<i class="fas fa-play-circle"></i>';
    overlay.appendChild(playIcon);
    
    card.appendChild(img);
    card.appendChild(overlay);
    return card;
}

function displayMovies(list = [], containerId, limit = 8) {
    console.log(`📺 displayMovies(${containerId}): ${list.length} items, showing ${limit}`);
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`❌ Container not found: ${containerId}`);
        return;
    }
    container.innerHTML = '';
    
    // Limit the number of movies displayed (1 row)
    const displayList = list.slice(0, limit);
    
    displayList.forEach((item, index) => {
        const card = buildMovieCard(item);
        container.appendChild(card);
        if (index < 3) console.log(`  - ${item.title} (${item.poster_url ? 'has poster' : 'NO POSTER'})`);
    });
    console.log(`✅ Rendered ${displayList.length}/${list.length} movies to #${containerId}`);
}

// ===== GENRES =====
async function loadGenres() {
    try {
        const res = await api.get(AppConfig.api.endpoints.genres);
        if (res && res.success) displayGenres(res.data || []);
    } catch (err) {
        logger.warn('loadGenres failed, using defaults', err);
        displayDefaultGenres();
    }
}

function displayGenres(genres) {
    const container = document.getElementById('genresGrid');
    if (!container) return;
    const icons = {
        'action': 'fa-fist-raised', 'adventure': 'fa-map-marked-alt', 'animation': 'fa-palette',
        'comedy': 'fa-laugh', 'crime': 'fa-user-secret', 'documentary': 'fa-file-video',
        'drama': 'fa-theater-masks', 'family': 'fa-users', 'fantasy': 'fa-hat-wizard',
        'horror': 'fa-ghost', 'mystery': 'fa-question-circle', 'romance': 'fa-heart',
        'sci-fi': 'fa-robot', 'thriller': 'fa-exclamation-triangle', 'war': 'fa-bomb'
    };
    container.innerHTML = '';
    genres.forEach(g => {
        const card = document.createElement('div');
        card.className = 'genre-card';
        // Use genre ID instead of slug for new API
        card.onclick = () => filterByGenreId(g.id, g.name);
        const i = document.createElement('i');
        i.className = `fas ${icons[g.slug] || 'fa-film'}`;
        const h3 = document.createElement('h3');
        h3.textContent = g.name;
        // Show movie count if available
        if (g.movie_count !== undefined) {
            const count = document.createElement('span');
            count.className = 'genre-count';
            count.textContent = `${g.movie_count} phim`;
            count.style.cssText = 'display:block; font-size:0.8em; color:#999; margin-top:5px;';
            card.appendChild(i);
            card.appendChild(h3);
            card.appendChild(count);
        } else {
            card.appendChild(i);
            card.appendChild(h3);
        }
        container.appendChild(card);
    });
}

function displayDefaultGenres() {
    const defaults = [
        {name: 'Hành động', slug: 'action'}, {name: 'Phiêu lưu', slug: 'adventure'},
        {name: 'Hoạt hình', slug: 'animation'}, {name: 'Hài', slug: 'comedy'},
        {name: 'Khoa học viễn tưởng', slug: 'sci-fi'}, {name: 'Kinh dị', slug: 'horror'}
    ];
    displayGenres(defaults);
}

// ===== SEARCH =====
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    const suggestionsDiv = document.getElementById('searchSuggestions');
    let searchTimeout = null;

    // Input event for live suggestions
    searchInput.addEventListener('input', (e) => {
        const q = e.target.value || '';
        clearTimeout(searchTimeout);
        if (q.trim().length >= 2) {
            searchTimeout = setTimeout(() => showSearchSuggestions(q), 300);
        } else {
            hideSuggestions();
            if (!q.trim()) {
                // Clear search, show all movies
                document.getElementById('searchResultsSection').style.display = 'none';
                document.querySelectorAll('.movie-row').forEach(row => { 
                    if (row.id !== 'searchResultsSection') row.style.display = 'block'; 
                });
                loadMovies();
            }
        }
    });

    // Enter key to show all search results
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query.length >= 2) {
                hideSuggestions();
                performFullSearch(query);
            }
        } else if (e.key === 'Escape') {
            hideSuggestions();
        }
    });

    // Click outside to hide suggestions
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            hideSuggestions();
        }
    });
}

async function showSearchSuggestions(query) {
    const suggestionsDiv = document.getElementById('searchSuggestions');
    if (!suggestionsDiv) return;
    suggestionsDiv.innerHTML = `<div class="suggestion-loading"><i class="fas fa-spinner fa-spin"></i><p>Đang tìm kiếm...</p></div>`;
    suggestionsDiv.classList.add('show');
    try {
        // Use new autocomplete endpoint for better suggestions
        const res = await api.get('/api/search/autocomplete', { q: query, limit: 5 });
        if (res && res.success && res.data.length) {
            suggestionsDiv.innerHTML = '';
            res.data.forEach(movie => {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.onclick = () => { goToMovie(movie.id); };
                const img = document.createElement('img');
                img.src = movie.poster_url || 'https://via.placeholder.com/50x70?text=No+Image';
                img.alt = movie.title;
                const info = document.createElement('div');
                info.className = 'suggestion-info';
                // Use highlighted title if available, otherwise regular title
                const displayTitle = movie.title_highlighted || Utils.sanitizeHTML(movie.title);
                info.innerHTML = `<div class="suggestion-title">${displayTitle}</div>`;
                item.appendChild(img);
                item.appendChild(info);
                suggestionsDiv.appendChild(item);
            });
            
            // Add "See all results" button
            const seeAllBtn = document.createElement('div');
            seeAllBtn.className = 'suggestion-see-all';
            seeAllBtn.innerHTML = `<i class="fas fa-search"></i> Xem tất cả kết quả cho "${Utils.sanitizeHTML(query)}" (Nhấn Enter)`;
            seeAllBtn.onclick = () => {
                hideSuggestions();
                performFullSearch(query);
            };
            suggestionsDiv.appendChild(seeAllBtn);
        } else {
            suggestionsDiv.innerHTML = `<div class="no-suggestions"><i class="fas fa-search"></i><p>Không tìm thấy kết quả phù hợp</p></div>`;
        }
    } catch (err) {
        logger.warn('search suggestions failed', err);
        suggestionsDiv.innerHTML = '';
        hideSuggestions();
    }
}

function hideSuggestions() {
    const suggestionsDiv = document.getElementById('searchSuggestions');
    if (!suggestionsDiv) return;
    suggestionsDiv.classList.remove('show');
    setTimeout(() => { suggestionsDiv.innerHTML = ''; }, 200);
}

// Full search - shows all results when Enter is pressed
async function performFullSearch(query) {
    if (!query || !query.trim()) {
        // Clear search, restore all content
        document.getElementById('searchResultsSection').style.display = 'none';
        document.querySelectorAll('.movie-row').forEach(row => { 
            if (row.id !== 'searchResultsSection') row.style.display = 'block'; 
        });
        loadMovies();
        return;
    }
    
    const searchResultsSection = document.getElementById('searchResultsSection');
    const searchResultsDiv = document.getElementById('searchResults');
    
    // Show loading
    searchResultsDiv.innerHTML = `
        <div class="search-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Đang tìm kiếm "${Utils.sanitizeHTML(query)}"...</p>
        </div>
    `;
    searchResultsSection.style.display = 'block';
    
    // Hide other sections
    document.querySelectorAll('.movie-row').forEach(row => { 
        if (row.id !== 'searchResultsSection') row.style.display = 'none'; 
    });
    
    try {
        // Use /api/movies with search parameter for fuzzy matching
        const res = await api.get(AppConfig.api.endpoints.movies, { 
            search: query, 
            per_page: 200  // Get more results for full search
        });
        
        if (res && res.success && res.data.length) {
            const total = res.total_count || res.data.length;
            document.querySelector('#searchResultsSection h2').innerHTML = 
                `🔍 Kết quả tìm kiếm cho "${Utils.sanitizeHTML(query)}" - ${total} phim`;
            displayMovies(res.data, 'searchResults');
        } else {
            searchResultsDiv.innerHTML = `
                <div class="no-search-results">
                    <i class="fas fa-search"></i>
                    <p>Không tìm thấy phim nào cho "${Utils.sanitizeHTML(query)}"</p>
                    <button onclick="clearSearch()" class="btn-primary">Xóa tìm kiếm</button>
                </div>
            `;
        }
    } catch (err) {
        logger.error('performFullSearch error', err);
        searchResultsDiv.innerHTML = `
            <div class="no-search-results">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Lỗi khi tìm kiếm!</p>
                <button onclick="clearSearch()" class="btn-primary">Thử lại</button>
            </div>
        `;
        notifications.error('Lỗi khi tìm kiếm!');
    }
}

function clearSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';
    document.getElementById('searchResultsSection').style.display = 'none';
    document.querySelectorAll('.movie-row').forEach(row => { 
        if (row.id !== 'searchResultsSection') row.style.display = 'block'; 
    });
    loadMovies();
}

async function performSearch(query) {
    // Alias for backward compatibility
    return performFullSearch(query);
}

// ===== MOVIE ACTIONS =====
function showMovieDetail(movieId) { window.location.href = `movie-detail.html?id=${movieId}`; }

function playMovie(movieId) {
    if (!currentUser) {
        notifications.warning('Vui lòng đăng nhập để xem phim!', 'Yêu cầu đăng nhập');
        setTimeout(() => window.location.href = 'login.html', 1400);
        return;
    }
    window.location.href = `player.html?id=${movieId}&v=${Date.now()}`;
}

async function toggleFavorite(movieId, event) {
    if (!currentUser) {
        notifications.warning('Vui lòng đăng nhập để thêm yêu thích!');
        setTimeout(() => window.location.href = 'login.html', 1200);
        return;
    }
    try {
        const isFav = userFavorites.includes(movieId);
        if (isFav) {
            const res = await api.delete(`${AppConfig.api.endpoints.favorites}/${movieId}`);
            if (res && res.success) {
                userFavorites = userFavorites.filter(id => id !== movieId);
                notifications.success('Đã xóa khỏi danh sách yêu thích');
                loadUserData();
            } else {
                notifications.error(res && res.error ? res.error : 'Không thể xóa khỏi yêu thích');
            }
        } else {
            const res = await api.post(AppConfig.api.endpoints.favorites, { movie_id: movieId });
            if (res && res.success) {
                userFavorites.push(movieId);
                notifications.success('Đã thêm vào danh sách yêu thích!');
                loadUserData();
            } else {
                notifications.error(res && res.error ? res.error : 'Không thể thêm vào yêu thích');
            }
        }
    } catch (err) {
        logger.error('toggleFavorite error', err);
        notifications.error('Có lỗi xảy ra!');
    }
}

function addToFavorites(movieId) { toggleFavorite(movieId); }

function filterByGenre(slug) { window.location.href = `browse.html?genre=${slug}`; }
function filterByGenreId(genreId, genreName) { 
    window.location.href = `browse.html?genre_id=${genreId}&genre_name=${encodeURIComponent(genreName)}`; 
}

// ===== USER DATA =====
async function loadUserData() {
    if (!currentUser) {
        const myListTop = document.getElementById('myListSection');
        if (myListTop) myListTop.style.display = 'none';
        document.getElementById('myListSectionBottom').style.display = 'none';
        document.getElementById('watchHistorySection').style.display = 'none';
        return;
    }
    try {
        // Load favorites
        const favRes = await api.get(AppConfig.api.endpoints.favorites);
        if (favRes && favRes.success) {
            userFavorites = (favRes.data || []).map(f => f.movie_id || f.id);
            const favorites = favRes.data || [];
            
            // Display in bottom My List section (all items)
            displayMyListBottom(favorites);
        }
        
        // Load watch history
        loadWatchHistory();
    } catch (err) {
        logger.warn('loadUserData failed', err);
    const myListTop = document.getElementById('myListSection');
    if (myListTop) myListTop.style.display = 'none';
    document.getElementById('myListSectionBottom').style.display = 'none';
    document.getElementById('watchHistorySection').style.display = 'none';
    }
}

function displayMyListBottom(favorites) {
    const container = document.getElementById('myListBottom');
    const section = document.getElementById('myListSectionBottom');
    if (!container || !section) return;

    if (!favorites || favorites.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    container.innerHTML = '';
    favorites.forEach(item => {
        const card = buildMovieCard(item);
        container.appendChild(card);
    });
}

async function loadWatchHistory() {
    if (!currentUser) {
        document.getElementById('watchHistorySection').style.display = 'none';
        return;
    }
    
    try {
        const res = await api.get(AppConfig.api.endpoints.watchHistory);
        if (res && res.success && res.data && res.data.length > 0) {
            displayWatchHistory(res.data);
        } else {
            document.getElementById('watchHistorySection').style.display = 'none';
        }
    } catch (err) {
        logger.warn('loadWatchHistory failed', err);
        document.getElementById('watchHistorySection').style.display = 'none';
    }
}

function displayWatchHistory(history) {
    const container = document.getElementById('watchHistory');
    const section = document.getElementById('watchHistorySection');
    if (!container || !section) return;

    if (!history || history.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    
    // Sort by last watched (most recent first)
    history.sort((a, b) => new Date(b.last_watched || b.updated_at) - new Date(a.last_watched || a.updated_at));
    
    // Display only first 8 items
    displayMovies(history, 'watchHistory', 8);
}

async function clearAllWatchHistory() {
    if (!currentUser) return;
    const ok = confirm('Bạn có chắc muốn xóa toàn bộ lịch sử xem?');
    if (!ok) return;
    try {
        const res = await api.delete(AppConfig.api.endpoints.watchHistory);
        if (res && res.success) {
            document.getElementById('watchHistorySection').style.display = 'none';
            document.getElementById('continueWatchingSection').style.display = 'none';
            notifications.success('Đã xóa toàn bộ lịch sử xem!', 'Lịch sử xem');
        } else {
            notifications.error(res && res.error ? res.error : 'Không thể xóa lịch sử');
        }
    } catch (err) {
        logger.error('clearAllWatchHistory error', err);
        notifications.error('Có lỗi xảy ra khi xóa lịch sử!', 'Lỗi');
    }
}

async function clearWatchHistory() {
    if (!currentUser) return;
    const ok = confirm('Bạn có chắc muốn xóa toàn bộ lịch sử xem?');
    if (!ok) return;
    try {
        const res = await api.delete(AppConfig.api.endpoints.watchHistory);
        if (res && res.success) {
            document.getElementById('continueWatchingSection').style.display = 'none';
            notifications.success('Đã xóa toàn bộ lịch sử xem!', 'Lịch sử xem');
        } else {
            notifications.error(res && res.error ? res.error : 'Không thể xóa lịch sử');
        }
    } catch (err) {
        logger.error('clearWatchHistory error', err);
        notifications.error('Có lỗi xảy ra khi xóa lịch sử!', 'Lỗi');
    }
}

// Minimal sidebar & hero loaders (non-blocking)
async function loadSidebarData() {
    try {
        const res = await api.get(AppConfig.api.endpoints.movies);
        if (!res || !res.success || !res.data) return;
        
        const allMovies = res.data;
        
        // Load Hot Movies (top rated, IMDb >= 8.0)
        const hotMovies = allMovies
            .filter(m => m.imdb_rating >= 8.0)
            .sort((a, b) => b.imdb_rating - a.imdb_rating)
            .slice(0, 5);
        
        displaySidebarMovies(hotMovies, 'hotMoviesList', true);
        
        // Load Most Watched (sorted by rating for now)
        const mostWatched = [...allMovies]
            .sort((a, b) => b.imdb_rating - a.imdb_rating)
            .slice(0, 5);
        
        displaySidebarMovies(mostWatched, 'mostWatchedList', false);
        
        logger.info('Sidebar data loaded successfully');
    } catch (err) {
        logger.error('loadSidebarData failed', err);
    }
}

function displaySidebarMovies(movies, containerId, showHotBadge) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    movies.forEach((movie, index) => {
        const item = document.createElement('div');
        item.className = 'sidebar-item';
        item.onclick = () => showMovieDetail(movie.id);
        
        const posterDiv = document.createElement('div');
        posterDiv.className = 'sidebar-item-poster';
        
        const img = document.createElement('img');
        img.src = movie.poster_url;
        img.alt = movie.title;
        img.loading = 'lazy';
        
        const rank = document.createElement('div');
        rank.className = 'sidebar-item-rank';
        rank.textContent = index + 1;
        
        posterDiv.appendChild(img);
        posterDiv.appendChild(rank);
        
        const info = document.createElement('div');
        info.className = 'sidebar-item-info';
        
        const title = document.createElement('div');
        title.className = 'sidebar-item-title';
        title.textContent = movie.title;
        
        const meta = document.createElement('div');
        meta.className = 'sidebar-item-meta';
        
        const rating = document.createElement('span');
        rating.className = 'rating';
        rating.innerHTML = `<i class="fas fa-star"></i> ${movie.imdb_rating}`;
        
        const year = document.createElement('span');
        year.className = 'year';
        year.textContent = movie.release_year;
        
        meta.appendChild(rating);
        meta.appendChild(year);
        
        const metaRow = document.createElement('div');
        metaRow.className = 'sidebar-item-meta';
        
        const badge = document.createElement('span');
        badge.className = movie.is_premium ? 'sidebar-item-badge premium' : 'sidebar-item-badge';
        badge.innerHTML = movie.is_premium ? '<i class="fas fa-crown"></i> Premium' : 'Free';
        
        metaRow.appendChild(badge);
        
        if (showHotBadge && index < 3) {
            const hotBadge = document.createElement('span');
            hotBadge.className = 'sidebar-item-badge hot';
            hotBadge.innerHTML = '<i class="fas fa-fire"></i> Hot';
            metaRow.appendChild(hotBadge);
        }
        
        info.appendChild(title);
        info.appendChild(meta);
        info.appendChild(metaRow);
        
        item.appendChild(posterDiv);
        item.appendChild(info);
        
        container.appendChild(item);
    });
}

// Hero Carousel State
let carouselSlides = [];
let currentSlideIndex = 0;
let carouselInterval = null;

async function loadHeroBanner() {
    try {
        // Load trending movies for hero banner (top viewed movies)
        const res = await api.get(AppConfig.api.endpoints.movies, { 
            per_page: 20,
            sort: 'views',
            order: 'desc',
            _cache_bust: Math.floor(Date.now() / 60000) // Cache bust every minute
        });
        
        if (res && res.success && res.data && res.data.length) {
            // Filter only movies with good ratings for better user experience
            const qualityMovies = res.data.filter(m => {
                const hasBackdrop = m.backdrop_url || m.poster_url;
                const hasRating = m.imdb_rating >= 6.0; // Only show well-rated movies
                return hasBackdrop && hasRating;
            });
            
            // Take top 8 for hero carousel
            carouselSlides = qualityMovies.slice(0, 8);
            
            // Fallback: if not enough quality movies, take any with backdrop
            if (carouselSlides.length < 5) {
                carouselSlides = res.data.filter(m => m.backdrop_url || m.poster_url).slice(0, 8);
            }
            
            initHeroCarousel();
        }
    } catch (err) {
        logger.warn('loadHeroBanner failed', err);
    }
}

function initHeroCarousel() {
    const carouselContainer = document.querySelector('.carousel-container');
    const indicatorsContainer = document.getElementById('carouselIndicators');
    
    if (!carouselContainer || !indicatorsContainer) return;
    
    // Create slides
    carouselContainer.innerHTML = '';
    indicatorsContainer.innerHTML = '';
    
    carouselSlides.forEach((movie, index) => {
        // Create slide
        const slide = document.createElement('div');
        slide.className = 'carousel-slide';
        if (index === 0) slide.classList.add('active');
        
        // Use backdrop for better quality, fallback to poster
        let backdropUrl = movie.backdrop_url || movie.poster_url || '';
        
        // If URL contains ophim CDN, try to get higher quality version
        if (backdropUrl.includes('ophim') || backdropUrl.includes('_next/image')) {
            // Replace quality params for higher resolution
            backdropUrl = backdropUrl.replace(/&w=\d+/g, '&w=1920').replace(/&q=\d+/g, '&q=90');
        }
        
        slide.style.backgroundImage = `url('${Utils.sanitizeHTML(backdropUrl)}')`;
        
        // Build movie info badges
        const rating = movie.imdb_rating ? `<span class="hero-rating"><i class="fas fa-star"></i> ${movie.imdb_rating}</span>` : '';
        const year = movie.release_year ? `<span class="hero-year">${movie.release_year}</span>` : '';
        const views = movie.views ? `<span class="hero-views"><i class="fas fa-eye"></i> ${formatViews(movie.views)} lượt xem</span>` : '';
        const genres = movie.genres ? `<span class="hero-genres">${Utils.sanitizeHTML(movie.genres.split(',').slice(0, 3).join(' • '))}</span>` : '';
        
        // Truncate description
        const description = movie.description || movie.synopsis || 'Không có mô tả';
        const shortDesc = description.length > 200 ? description.substring(0, 200) + '...' : description;
        
        slide.innerHTML = `
            <div class="carousel-content">
                <div class="hero-badge">🔥 TRENDING</div>
                <h1>${Utils.sanitizeHTML(movie.title || '')}</h1>
                <div class="hero-meta">
                    ${rating}
                    ${year}
                    ${views}
                </div>
                ${genres ? `<div class="hero-genres-line">${genres}</div>` : ''}
                <p class="hero-description">${Utils.sanitizeHTML(shortDesc)}</p>
                <div class="hero-buttons">
                    <button class="btn btn-play" onclick="goToMovie(${movie.id})">
                        <i class="fas fa-play"></i> Xem ngay
                    </button>
                    <button class="btn btn-info" onclick="goToMovie(${movie.id})">
                        <i class="fas fa-info-circle"></i> Chi tiết
                    </button>
                </div>
            </div>
        `;
        
        carouselContainer.appendChild(slide);
        
        // Create indicator
        const indicator = document.createElement('div');
        indicator.className = 'carousel-indicator';
        if (index === 0) indicator.classList.add('active');
        indicator.onclick = () => goToSlide(index);
        indicatorsContainer.appendChild(indicator);
    });
    
    // Setup controls
    const prevBtn = document.getElementById('carouselPrev');
    const nextBtn = document.getElementById('carouselNext');
    
    if (prevBtn) prevBtn.onclick = () => changeSlide(-1);
    if (nextBtn) nextBtn.onclick = () => changeSlide(1);
    
    // Auto-play carousel
    startCarouselAutoPlay();
}

function changeSlide(direction) {
    const slides = document.querySelectorAll('.carousel-slide');
    const indicators = document.querySelectorAll('.carousel-indicator');
    
    if (slides.length === 0) return;
    
    // Remove active class
    slides[currentSlideIndex].classList.remove('active');
    indicators[currentSlideIndex].classList.remove('active');
    
    // Calculate new index
    currentSlideIndex = (currentSlideIndex + direction + slides.length) % slides.length;
    
    // Add active class
    slides[currentSlideIndex].classList.add('active');
    indicators[currentSlideIndex].classList.add('active');
    
    // Reset auto-play
    resetCarouselAutoPlay();
}

function goToSlide(index) {
    const slides = document.querySelectorAll('.carousel-slide');
    const indicators = document.querySelectorAll('.carousel-indicator');
    
    if (slides.length === 0 || index === currentSlideIndex) return;
    
    // Remove active class
    slides[currentSlideIndex].classList.remove('active');
    indicators[currentSlideIndex].classList.remove('active');
    
    // Set new index
    currentSlideIndex = index;
    
    // Add active class
    slides[currentSlideIndex].classList.add('active');
    indicators[currentSlideIndex].classList.add('active');
    
    // Reset auto-play
    resetCarouselAutoPlay();
}

function startCarouselAutoPlay() {
    carouselInterval = setInterval(() => {
        changeSlide(1);
    }, 5000); // Change every 5 seconds
}

function resetCarouselAutoPlay() {
    if (carouselInterval) {
        clearInterval(carouselInterval);
    }
    startCarouselAutoPlay();
}

// Pause carousel on hover
document.addEventListener('DOMContentLoaded', () => {
    const carousel = document.querySelector('.hero-carousel');
    if (carousel) {
        carousel.addEventListener('mouseenter', () => {
            if (carouselInterval) {
                clearInterval(carouselInterval);
            }
        });
        
        carousel.addEventListener('mouseleave', () => {
            startCarouselAutoPlay();
        });
    }
});

function goToMovie(id) { window.location.href = `movie-detail.html?id=${id}`; }

// Format view count (e.g., 1500 -> 1.5K)
function formatViews(views) {
    if (views >= 1000000) {
        return (views / 1000000).toFixed(1) + 'M';
    } else if (views >= 1000) {
        return (views / 1000).toFixed(1) + 'K';
    }
    return views.toString();
}

// User Menu Actions
function showProfile() {
    if (!currentUser) {
        window.location.href = '/login.html';
        return;
    }
    window.location.href = 'profile.html';
}

function showSubscription() {
    if (!currentUser) {
        window.location.href = '/login.html';
        return;
    }
    window.location.href = 'subscription.html';
}

function showSettings() {
    if (!currentUser) {
        window.location.href = '/login.html';
        return;
    }
    window.location.href = 'settings.html';
}

async function logout() {
    if (!currentUser) {
        window.location.href = '/login.html?logout=true';
        return;
    }
    
    try {
        await auth.logout();
        notifications.success('Đăng xuất thành công!', 'Hẹn gặp lại');
        setTimeout(() => {
            window.location.href = '/login.html?logout=true';
        }, 1000);
    } catch (error) {
        console.error('Logout error:', error);
        notifications.error('Có lỗi khi đăng xuất', 'Lỗi');
        // Even on error, redirect to login
        setTimeout(() => {
            window.location.href = '/login.html?logout=true';
        }, 1500);
    }
}

// Convenience functions (kept for compatibility with some legacy callers)
function showSuccessToast(message, title) { return showToast(message, 'success', title); }
function showErrorToast(message, title) { return showToast(message, 'error', title); }
function showWarningToast(message, title) { return showToast(message, 'warning', title); }
function showInfoToast(message, title) { return showToast(message, 'info', title); }

