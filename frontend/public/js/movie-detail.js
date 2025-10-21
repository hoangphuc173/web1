// Movie Detail Page JavaScript
let currentMovie = null;
let currentUser = null;
let selectedRating = 0;
let isFavorited = false;
let selectedEpisode = 1; // Default episode

// ===== TOAST NOTIFICATIONS =====
function createToastContainer() {
    if (!document.getElementById('toastContainer')) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
}

function showToast(message, type = 'info', title = '', duration = 3000) {
    createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <div class="toast-content">
            ${title ? `<div class="toast-title">${title}</div>` : ''}
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function showSuccessToast(message, title = 'Thành công') {
    showToast(message, 'success', title);
}

function showErrorToast(message, title = 'Lỗi') {
    showToast(message, 'error', title);
}

function showWarningToast(message, title = 'Cảnh báo', duration = 5000) {
    showToast(message, 'warning', title, duration);
}

function showLoginToast(message = 'Vui lòng đăng nhập để tiếp tục!') {
    createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = 'toast toast-warning';
    
    toast.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <div class="toast-content">
            <div class="toast-title">Yêu cầu đăng nhập</div>
            <div class="toast-message">${message}</div>
            <button class="toast-login-btn" onclick="window.location.href='/login.html'">
                Đăng nhập ngay
            </button>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, 8000); // 8 seconds for login toast
}

function showInfoToast(message, title = 'Thông tin') {
    showToast(message, 'info', title);
}

// Initialize page - Wait for core modules
if (typeof initializePage === 'function') {
    // Use core system
    initializePage('Movie Detail', async () => {
        createToastContainer();
        
        // Get movie ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const movieId = urlParams.get('id');
        
        if (!movieId) {
            showErrorToast('Không tìm thấy phim!');
            setTimeout(() => window.location.href = '/', 2000);
            return;
        }

        // Wait for the initial authentication check to complete
        await auth.initPromise;
        currentUser = auth.getCurrentUser();

        if (currentUser) {
            console.log('✅ User logged in:', currentUser.name || currentUser.email);
        } else {
            console.log('⚠️ No user logged in');
        }

        // Load movie details
        loadMovieDetails(movieId);
        loadReviews(movieId);
        loadComments(movieId);
        loadRelatedMovies(movieId);

        // Navbar scroll effect
        setupNavbarScroll();
        
        // Setup event listeners
        setupEventListeners();
    });
} else {
    // Fallback for standalone mode
    document.addEventListener('DOMContentLoaded', () => {
        createToastContainer();
        
        // Get movie ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const movieId = urlParams.get('id');
        
        if (!movieId) {
            showErrorToast('Không tìm thấy phim!');
            setTimeout(() => window.location.href = '/', 2000);
            return;
        }

        // Load user data - try smartStorage first, even in fallback mode
        try {
            if (typeof smartStorage !== 'undefined') {
                currentUser = smartStorage.get('currentUser');
                console.log('Fallback mode - loaded user from smartStorage:', currentUser);
            } else {
                console.warn('⚠️ Fallback mode - smartStorage not available!');
                currentUser = null;
            }
        } catch (e) {
            console.error('Fallback mode - error loading user:', e);
            currentUser = null;
        }
        
        if (currentUser) {
            console.log('✅ User logged in:', currentUser.name || currentUser.email);
        } else {
            console.log('⚠️ No user logged in');
        }

        // Load movie details
        loadMovieDetails(movieId);
        loadReviews(movieId);
        loadComments(movieId);
        loadRelatedMovies(movieId);

        // Navbar scroll effect
        setupNavbarScroll();
        
        // Setup event listeners
        setupEventListeners();
    });
}

function setupNavbarScroll() {
    window.addEventListener('scroll', () => {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

function setupEventListeners() {
    // Stars input for review modal
    const starsInput = document.querySelectorAll('#starsInput i');
    starsInput.forEach(star => {
        star.addEventListener('click', () => {
            const rating = parseInt(star.getAttribute('data-rating'));
            setRating(rating);
        });
    });
}

// Load movie details
async function loadMovieDetails(movieId) {
    try {
        const response = await fetch(`/api/movies/${movieId}`);
        const data = await response.json();
        
        if (data.success && data.data) {
            currentMovie = data.data;
            displayMovieDetails(currentMovie);
            checkIfFavorite(movieId);
        } else {
            throw new Error('Movie not found');
        }
    } catch (error) {
        console.error('Error loading movie:', error);
        showErrorToast('Không thể tải thông tin phim!');
        setTimeout(() => window.location.href = '/', 2000);
    }
}

// Display movie details
function displayMovieDetails(movie) {
    // Set backdrop
    const heroBackdrop = document.querySelector('.hero-backdrop');
    if (movie.backdrop_url) {
        heroBackdrop.style.backgroundImage = `url(${movie.backdrop_url})`;
    }

    // Set poster with proxy fallback
    const posterImg = document.getElementById('moviePoster');
    const posterUrl = movie.poster_url || 'https://via.placeholder.com/300x450?text=No+Image';
    posterImg.src = posterUrl;
    posterImg.alt = movie.title;
    posterImg.onerror = function() {
        if (movie.poster_url && !this.src.includes('/api/image-proxy')) {
            this.src = `/api/image-proxy?url=${encodeURIComponent(movie.poster_url)}`;
            this.onerror = function() {
                this.src = 'https://via.placeholder.com/300x450?text=No+Image';
                this.onerror = null;
            };
        } else {
            this.src = 'https://via.placeholder.com/300x450?text=No+Image';
            this.onerror = null;
        }
    };

    // Set title and info
    document.getElementById('movieTitle').textContent = movie.title;
    document.getElementById('movieOriginal').textContent = movie.original_title || movie.title;
    document.getElementById('movieRating').textContent = movie.imdb_rating || '0.0';
    document.getElementById('movieYear').textContent = movie.release_year || '2024';
    document.getElementById('movieDuration').textContent = `${movie.duration || 120} phút`;
    document.getElementById('movieQuality').textContent = movie.video_quality || 'HD';
    document.getElementById('movieDescription').textContent = movie.description || 'Chưa có mô tả';

    // Premium badge
    if (movie.is_premium) {
        document.getElementById('premiumBadge').style.display = 'inline-flex';
    }

    // Movie details
    document.getElementById('movieDirector').textContent = movie.director || '-';
    document.getElementById('movieCast').textContent = movie.cast || '-';
    document.getElementById('movieGenres').textContent = movie.genres || '-';
    document.getElementById('movieCountry').textContent = movie.country || '-';

    // Display episodes if it's a series
    if (movie.type === 'series' || movie.episodes) {
        displayEpisodes(movie);
    }

    // Display cast (sample data)
    displayCast(movie.cast);
}

// Display cast members
function displayCast(castString) {
    const castGrid = document.getElementById('castGrid');
    castGrid.innerHTML = '';

    if (!castString) return;

    const castList = castString.split(',').slice(0, 6).map(name => name.trim());
    
    castList.forEach(name => {
        const castMember = document.createElement('div');
        castMember.className = 'cast-member';
        
        const initials = name.split(' ').map(n => n[0]).join('');
        const avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&size=150&background=random`;
        
        castMember.innerHTML = `
            <img src="${avatarUrl}" alt="${name}">
            <div class="name">${name}</div>
            <div class="role">Diễn viên</div>
        `;
        
        castGrid.appendChild(castMember);
    });
}

// Display episodes for TV series
function displayEpisodes(movie) {
    console.log('🎬 displayEpisodes called for:', movie.title);
    console.log('   Movie type:', movie.type);
    console.log('   Has episodes?', !!movie.episodes);
    
    const episodesSection = document.getElementById('episodesSection');
    const episodesGrid = document.getElementById('episodesGrid');
    
    if (!episodesSection || !episodesGrid) {
        console.error('❌ Episodes section or grid not found in DOM');
        return;
    }
    
    console.log('✅ Episodes section found');
    
    // Only show episodes for series type
    if (movie.type !== 'series') {
        console.log('⚠️ Not a series, hiding episodes section');
        episodesSection.style.display = 'none';
        return;
    }
    
    console.log('✅ This is a series');
    
    let episodes = [];
    
    // Try to get episodes from API response
    if (movie.episodes && Array.isArray(movie.episodes)) {
        episodes = movie.episodes;
        console.log(`✅ Found ${episodes.length} episodes from API`);
    } 
    // Fallback: check if episodes has server_data structure (OPhim format)
    else if (movie.episodes && typeof movie.episodes === 'object') {
        if (movie.episodes.items && Array.isArray(movie.episodes.items)) {
            episodes = movie.episodes.items;
        }
        else if (movie.episodes.server_data && Array.isArray(movie.episodes.server_data)) {
            episodes = movie.episodes.server_data[0]?.items || [];
        }
    }
    
    // Only show episodes section if we have episodes
    if (episodes.length > 0) {
        episodesSection.style.display = 'block';
        episodesGrid.innerHTML = '';
        
        console.log(`📺 Displaying ${episodes.length} episodes for series: ${movie.title}`);
        
        episodes.forEach((episode, index) => {
            const episodeNum = episode.episode_number || parseInt(episode.name?.match(/\d+/)?.[0]) || (index + 1);
            const episodeCard = document.createElement('div');
            episodeCard.className = 'episode-card';
            
            // Set first episode as active by default
            if (episodeNum == selectedEpisode) {
                episodeCard.classList.add('active');
            }
            
            episodeCard.innerHTML = `
                <div class="episode-number">${episodeNum}</div>
                <div class="episode-title">${episode.name || `Tập ${episodeNum}`}</div>
                <i class="fas fa-play play-icon"></i>
            `;
            
            episodeCard.addEventListener('click', (e) => {
                console.log('Episode card clicked:', episodeNum);
                console.log('Redirecting to player...');
                
                // Check if user is logged in
                let isLoggedIn = false;
                try {
                    if (typeof auth !== 'undefined' && auth.isAuthenticated) {
                        isLoggedIn = auth.isAuthenticated();
                    } else if (currentUser) {
                        isLoggedIn = true;
                    } else if (typeof smartStorage !== 'undefined') {
                        const user = smartStorage.get('currentUser');
                        isLoggedIn = !!user;
                    } else {
                        const userStr = sessionStorage.getItem('cgv_currentUser') || sessionStorage.getItem('currentUser');
                        isLoggedIn = !!userStr;
                    }
                } catch (error) {
                    console.error('Error checking auth:', error);
                    isLoggedIn = !!currentUser;
                }
                
                if (!isLoggedIn) {
                    console.warn('❌ User not logged in');
                    showLoginToast('Bạn cần đăng nhập để xem phim này!');
                    return;
                }
                
                // Update selected episode
                selectedEpisode = episodeNum;
                console.log('✅ Selected episode:', selectedEpisode);
                
                // Visual feedback before redirect
                episodeCard.style.transform = 'scale(0.95)';
                
                // Redirect to player after short delay for visual feedback
                setTimeout(() => {
                    const url = `/player.html?id=${currentMovie.id}&episode=${episodeNum}&v=${Date.now()}`;
                    console.log('Redirecting to:', url);
                    window.location.href = url;
                }, 150);
            });
            
            episodesGrid.appendChild(episodeCard);
        });
    } else {
        // No episodes found, hide the section
        episodesSection.style.display = 'none';
        console.log(`ℹ️ No episodes found for: ${movie.title} (Type: ${movie.type})`);
    }
}

// Load related movies
async function loadRelatedMovies(movieId) {
    try {
        const response = await fetch('/api/movies');
        const data = await response.json();
        
        if (data.success && data.data) {
            // Filter out current movie and get random 6 movies
            const otherMovies = data.data.filter(m => m.id !== parseInt(movieId));
            const relatedMovies = otherMovies.sort(() => 0.5 - Math.random()).slice(0, 6);
            displayRelatedMovies(relatedMovies);
        }
    } catch (error) {
        console.error('Error loading related movies:', error);
    }
}

// Display related movies
function displayRelatedMovies(movies) {
    const relatedGrid = document.getElementById('relatedMovies');
    relatedGrid.innerHTML = '';

    movies.forEach(movie => {
        const movieCard = document.createElement('div');
        movieCard.className = 'movie-card';
        movieCard.onclick = () => window.location.href = `/movie-detail.html?id=${movie.id}`;
        
        movieCard.innerHTML = `
            <img src="${movie.poster_url || 'https://via.placeholder.com/200x300'}" alt="${movie.title}">
            <h3>${movie.title}</h3>
        `;
        
        relatedGrid.appendChild(movieCard);
    });
}

// Load reviews
async function loadReviews(movieId) {
    try {
        const response = await fetch(`/api/reviews?movie_id=${movieId}`);
        const data = await response.json();
        
        if (data.success && data.data) {
            displayReviews(data.data);
            calculateRatingSummary(data.data);
        }
    } catch (error) {
        console.error('Error loading reviews:', error);
    }
}

// Display reviews
function displayReviews(reviews) {
    const reviewsList = document.getElementById('reviewsList');
    const reviewCount = document.getElementById('reviewCount');
    
    reviewCount.textContent = reviews.length;
    reviewsList.innerHTML = '';

    if (reviews.length === 0) {
        reviewsList.innerHTML = '<p style="text-align: center; color: #888;">Chưa có đánh giá nào. Hãy là người đầu tiên!</p>';
        return;
    }

    reviews.forEach(review => {
        const reviewItem = document.createElement('div');
        reviewItem.className = 'review-item';
        
        const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
        const date = new Date(review.created_at).toLocaleDateString('vi-VN');
        
        reviewItem.innerHTML = `
            <div class="review-header">
                <div class="user-info">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(review.user_name)}&background=e50914&color=fff" alt="${review.user_name}">
                    <div>
                        <div class="name">${review.user_name}</div>
                        <div class="date">${date}</div>
                    </div>
                </div>
                <div class="review-rating">
                    ${stars}
                </div>
            </div>
            <div class="review-text">${review.review_text || 'Không có nhận xét'}</div>
        `;
        
        reviewsList.appendChild(reviewItem);
    });
}

// Calculate rating summary
function calculateRatingSummary(reviews) {
    if (reviews.length === 0) {
        document.getElementById('avgRating').textContent = '0.0';
        document.getElementById('ratingCount').textContent = '0 đánh giá';
        return;
    }

    // Calculate average
    const total = reviews.reduce((sum, r) => sum + r.rating, 0);
    const average = (total / reviews.length).toFixed(1);
    document.getElementById('avgRating').textContent = average;
    document.getElementById('ratingCount').textContent = `${reviews.length} đánh giá`;

    // Update stars display
    const avgStars = document.getElementById('avgStars');
    avgStars.innerHTML = '';
    for (let i = 1; i <= 5; i++) {
        const icon = document.createElement('i');
        icon.className = i <= Math.round(average) ? 'fas fa-star' : 'far fa-star';
        avgStars.appendChild(icon);
    }

    // Calculate rating distribution
    const distribution = [0, 0, 0, 0, 0];
    reviews.forEach(r => {
        distribution[r.rating - 1]++;
    });

    // Update rating bars
    for (let i = 1; i <= 5; i++) {
        const count = distribution[i - 1];
        const percent = reviews.length > 0 ? (count / reviews.length * 100).toFixed(0) : 0;
        document.getElementById(`bar${i}`).style.width = `${percent}%`;
        document.getElementById(`percent${i}`).textContent = `${percent}%`;
    }
}

// Load comments
async function loadComments(movieId) {
    try {
        const response = await fetch(`/api/comments?movie_id=${movieId}`);
        const data = await response.json();
        
        if (data.success && data.data) {
            displayComments(data.data);
        }
    } catch (error) {
        console.error('Error loading comments:', error);
    }
}

// Display comments
function displayComments(comments) {
    const commentsList = document.getElementById('commentsList');
    const commentCount = document.getElementById('commentCount');
    
    commentCount.textContent = comments.length;
    commentsList.innerHTML = '';

    if (comments.length === 0) {
        commentsList.innerHTML = '<p style="text-align: center; color: #888;">Chưa có bình luận nào.</p>';
        return;
    }

    comments.forEach(comment => {
        const commentItem = document.createElement('div');
        commentItem.className = 'comment-item';
        
        const date = new Date(comment.created_at).toLocaleDateString('vi-VN');
        
        commentItem.innerHTML = `
            <div class="comment-header">
                <div class="user-info">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(comment.user_name)}&background=e50914&color=fff" alt="${comment.user_name}">
                    <div>
                        <div class="name">${comment.user_name}</div>
                        <div class="date">${date}</div>
                    </div>
                </div>
            </div>
            <div class="comment-text">${comment.comment_text}</div>
        `;
        
        commentsList.appendChild(commentItem);
    });
}

// Switch tab
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

// Play movie
function playMovie() {
    if (!currentMovie) {
        showErrorToast('Không tìm thấy thông tin phim!');
        return;
    }

    // Check if user is logged in using the auth module
    let isLoggedIn = false;
    try {
        // Try auth module first
        if (typeof auth !== 'undefined' && auth.isAuthenticated) {
            isLoggedIn = auth.isAuthenticated();
        }
        // Fallback to check currentUser or smartStorage
        else if (currentUser) {
            isLoggedIn = true;
        }
        else if (typeof smartStorage !== 'undefined') {
            const user = smartStorage.get('currentUser');
            isLoggedIn = !!user;
        }
        else {
            // Last resort: check sessionStorage
            const userStr = sessionStorage.getItem('cgv_currentUser') || sessionStorage.getItem('currentUser');
            isLoggedIn = !!userStr;
        }
    } catch (error) {
        console.error('Error checking auth:', error);
        isLoggedIn = !!currentUser;
    }

    if (!isLoggedIn) {
        console.warn('❌ User not logged in, showing login prompt');
        showLoginToast('Bạn cần đăng nhập để xem phim này!');
        return;
    }

    console.log('✅ User verified, redirecting to player');
    console.log('Selected episode:', selectedEpisode);
    
    // Redirect to player with movie ID and episode number
    try {
        const url = `/player.html?id=${currentMovie.id}&episode=${selectedEpisode}&v=${Date.now()}`;
        console.log('Redirecting to:', url);
        window.location.href = url;
    } catch (error) {
        console.error('Error redirecting to player:', error);
        showErrorToast('Không thể mở trình phát. Vui lòng thử lại!');
    }
}

// Play trailer
function playTrailer() {
    if (!currentMovie || !currentMovie.trailer_url) {
        showWarningToast('Trailer chưa có sẵn!');
        return;
    }

    // Extract YouTube video ID
    let videoId = '';
    if (currentMovie.trailer_url.includes('youtube.com/watch?v=')) {
        videoId = currentMovie.trailer_url.split('v=')[1].split('&')[0];
    } else if (currentMovie.trailer_url.includes('youtu.be/')) {
        videoId = currentMovie.trailer_url.split('youtu.be/')[1];
    }

    if (videoId) {
        document.getElementById('trailerFrame').src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
        document.getElementById('trailerModal').classList.add('active');
    }
}

// Close trailer modal
function closeTrailerModal() {
    document.getElementById('trailerModal').classList.remove('active');
    document.getElementById('trailerFrame').src = '';
}

// Toggle favorite
async function toggleFavorite() {
    if (!currentUser) {
        showLoginToast('Đăng nhập để lưu phim vào danh sách yêu thích!');
        return;
    }

    if (!currentMovie) return;

    // Get both buttons: favorite (heart on poster) and bookmark (action button)
    const heartBtn = document.querySelector('.btn-favorite');
    const bookmarkBtn = document.querySelector('.btn-icon[title="Thêm vào danh sách"]');
    const heartIcon = heartBtn ? heartBtn.querySelector('i') : null;
    const bookmarkIcon = bookmarkBtn ? bookmarkBtn.querySelector('i') : null;

    try {
        if (isFavorited) {
            // Remove from favorites - user_id is handled by session
            const response = await api.delete(`/api/favorites/${currentMovie.id}`);

            if (response.success) {
                isFavorited = false;
                // Update heart button (poster)
                if (heartBtn) heartBtn.classList.remove('active');
                if (heartIcon) heartIcon.className = 'far fa-heart';
                // Update bookmark button (actions)
                if (bookmarkBtn) bookmarkBtn.classList.remove('active');
                if (bookmarkIcon) bookmarkIcon.className = 'far fa-bookmark';
                showSuccessToast('Đã xóa khỏi danh sách yêu thích');
            } else {
                showErrorToast(response.error || 'Không thể xóa');
            }
        } else {
            // Add to favorites - user_id is handled by session
            const response = await api.post('/api/favorites', {
                movie_id: currentMovie.id
            });
            
            if (response.success) {
                isFavorited = true;
                // Update heart button (poster)
                if (heartBtn) heartBtn.classList.add('active');
                if (heartIcon) heartIcon.className = 'fas fa-heart';
                // Update bookmark button (actions)
                if (bookmarkBtn) bookmarkBtn.classList.add('active');
                if (bookmarkIcon) bookmarkIcon.className = 'fas fa-bookmark';
                showSuccessToast('Đã thêm vào danh sách yêu thích!');
            } else {
                showErrorToast(response.error || 'Không thể thêm');
            }
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
        showErrorToast('Có lỗi xảy ra!');
    }
}

// Check if movie is in favorites
async function checkIfFavorite(movieId) {
    if (!currentUser) return;

    try {
        // user_id is handled by the session on the backend
        const response = await api.get(`/api/favorites`);
        
        if (response.success && response.data) {
            const favoriteCheck = response.data.some(fav => fav.movie_id === parseInt(movieId));
            isFavorited = favoriteCheck;
            
            // Update heart button (poster)
            const heartBtn = document.querySelector('.btn-favorite');
            const heartIcon = heartBtn ? heartBtn.querySelector('i') : null;
            
            // Update bookmark button (actions)
            const bookmarkBtn = document.querySelector('.btn-icon[title="Thêm vào danh sách"]');
            const bookmarkIcon = bookmarkBtn ? bookmarkBtn.querySelector('i') : null;
            
            if (favoriteCheck) {
                if (heartBtn) heartBtn.classList.add('active');
                if (heartIcon) heartIcon.className = 'fas fa-heart';
                if (bookmarkBtn) bookmarkBtn.classList.add('active');
                if (bookmarkIcon) bookmarkIcon.className = 'fas fa-bookmark';
            } else {
                if (heartBtn) heartBtn.classList.remove('active');
                if (heartIcon) heartIcon.className = 'far fa-heart';
                if (bookmarkBtn) bookmarkBtn.classList.remove('active');
                if (bookmarkIcon) bookmarkIcon.className = 'far fa-bookmark';
            }
        }
    } catch (error) {
        console.error('Error checking favorite:', error);
    }
}

// Share movie
function shareMovie() {
    const url = window.location.href;
    const title = currentMovie ? currentMovie.title : 'Phim hay';
    
    if (navigator.share) {
        navigator.share({
            title: title,
            text: `Xem phim ${title}`,
            url: url
        });
        showSuccessToast('Đã chia sẻ thành công!');
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(url);
        showSuccessToast('Đã sao chép link vào clipboard!');
    }
}

// Review modal
function openReviewModal() {
    if (!currentUser) {
        showLoginToast('Đăng nhập để đánh giá phim này!');
        return;
    }
    document.getElementById('reviewModal').classList.add('active');
}

function closeReviewModal() {
    document.getElementById('reviewModal').classList.remove('active');
    selectedRating = 0;
    document.querySelectorAll('#starsInput i').forEach(star => {
        star.classList.remove('active');
    });
    document.getElementById('reviewText').value = '';
}

function setRating(rating) {
    selectedRating = rating;
    const stars = document.querySelectorAll('#starsInput i');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

// Submit review
async function submitReview() {
    if (!currentUser) {
        showLoginToast('Vui lòng đăng nhập!');
        return;
    }

    if (selectedRating === 0) {
        showWarningToast('Vui lòng chọn số sao đánh giá!');
        return;
    }

    const reviewText = document.getElementById('reviewText').value.trim();

    try {
        // user_id is handled by the session on the backend
        const response = await api.post('/api/reviews', {
            movie_id: currentMovie.id,
            rating: selectedRating,
            review_text: reviewText
        });
        
        if (response.success) {
            showSuccessToast('Đã gửi đánh giá thành công!');
            closeReviewModal();
            loadReviews(currentMovie.id);
        } else {
            showErrorToast(response.error || 'Có lỗi xảy ra!');
        }
    } catch (error) {
        console.error('Error submitting review:', error);
        showErrorToast('Không thể gửi đánh giá!');
    }
}

// Post comment
async function postComment() {
    if (!currentUser) {
        showLoginToast('Đăng nhập để bình luận!');
        return;
    }

    const commentText = document.getElementById('commentText').value.trim();
    
    if (!commentText) {
        showWarningToast('Vui lòng nhập nội dung bình luận!');
        return;
    }

    try {
        // user_id is handled by the session on the backend
        const response = await api.post('/api/comments', {
            movie_id: currentMovie.id,
            comment_text: commentText
        });
        
        if (response.success) {
            document.getElementById('commentText').value = '';
            loadComments(currentMovie.id);
            showSuccessToast('Đã gửi bình luận thành công!');
        } else {
            showErrorToast(response.error || 'Có lỗi xảy ra!');
        }
    } catch (error) {
        console.error('Error posting comment:', error);
        showErrorToast('Không thể gửi bình luận!');
    }
}

// Logout
async function logout() {
    try {
        if (typeof auth !== 'undefined' && auth.logout) {
            await auth.logout();
            notifications.success('Đăng xuất thành công!', 'Hẹn gặp lại');
        } else {
            // Fallback: clear localStorage
            localStorage.removeItem('cgv_currentUser');
            localStorage.removeItem('cgv_authToken');
        }
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

// Toggle search
function toggleSearch() {
    const modal = document.getElementById('searchModal');
    modal.classList.add('active');
    const searchInput = document.getElementById('searchInput');
    searchInput.focus();
    searchInput.value = '';
    document.getElementById('searchResults').innerHTML = '';
}

// Close search
function closeSearch() {
    const modal = document.getElementById('searchModal');
    modal.classList.remove('active');
    document.getElementById('searchInput').value = '';
    document.getElementById('searchResults').innerHTML = '';
}

// Search movies
let searchTimeout;
async function searchMovies(query) {
    clearTimeout(searchTimeout);
    
    if (!query || query.trim().length < 2) {
        document.getElementById('searchResults').innerHTML = '';
        return;
    }

    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`/api/movies?search=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.success && data.data.length > 0) {
                displaySearchResults(data.data);
            } else {
                document.getElementById('searchResults').innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <p>Không tìm thấy kết quả cho "${query}"</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Search error:', error);
            showErrorToast('Lỗi khi tìm kiếm!');
        }
    }, 300); // Debounce 300ms
}

// Display search results
function displaySearchResults(movies) {
    const resultsContainer = document.getElementById('searchResults');
    
    resultsContainer.innerHTML = `
        <div class="results-count">Tìm thấy ${movies.length} kết quả</div>
        <div class="results-grid">
            ${movies.map(movie => `
                <div class="search-result-item" onclick="goToMovie(${movie.id})">
                    <img src="${movie.poster_url || '/placeholder.jpg'}" alt="${movie.title}" onerror="this.src='/placeholder.jpg'">
                    <div class="result-info">
                        <h4>${movie.title}</h4>
                        <div class="result-meta">
                            <span><i class="fas fa-calendar"></i> ${movie.release_year || 'N/A'}</span>
                            <span><i class="fas fa-star"></i> ${movie.imdb_rating || 'N/A'}</span>
                            <span class="badge">${movie.type === 'movie' ? 'Phim' : 'Series'}</span>
                        </div>
                        <p class="result-desc">${movie.description ? (movie.description.substring(0, 100) + '...') : 'Không có mô tả'}</p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Go to movie detail
function goToMovie(movieId) {
    window.location.href = `/movie-detail.html?id=${movieId}`;
}

// Add event listener for search input
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchMovies(e.target.value);
        });
        
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeSearch();
            }
        });
    }
    
    // Close search when clicking outside
    const searchModal = document.getElementById('searchModal');
    if (searchModal) {
        searchModal.addEventListener('click', (e) => {
            if (e.target === searchModal) {
                closeSearch();
            }
        });
    }
});

// User Menu Actions
function showProfile() {
    const currentUser = auth.getCurrentUser();
    if (!currentUser) {
        window.location.href = '/login.html';
        return;
    }
    notifications.info('Tính năng đang phát triển', 'Tài khoản');
    // TODO: Implement profile page
}

function showSubscription() {
    const currentUser = auth.getCurrentUser();
    if (!currentUser) {
        window.location.href = '/login.html';
        return;
    }
    notifications.info('Tính năng nâng cấp VIP đang phát triển', 'VIP');
    // TODO: Implement subscription page
}

function showSettings() {
    const currentUser = auth.getCurrentUser();
    if (!currentUser) {
        window.location.href = '/login.html';
        return;
    }
    notifications.info('Tính năng cài đặt đang phát triển', 'Cài đặt');
    // TODO: Implement settings page
}
