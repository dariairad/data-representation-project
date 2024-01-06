function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const loginData = {
        username: username,
        password: password
    };

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(loginData)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Login failed');
        }
    })
    .then(data => {
        // Store the JWT token securely in localStorage
        localStorage.setItem('jwtToken', data.access_token);

        // Redirect to a protected page or perform any other actions
        window.location.href = '/protected'; // Redirect to a protected page
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Login failed. Please check your credentials.");
    });
}

function getJwtToken() {
    return localStorage.getItem('jwtToken');
}


let currentPage = 1;
let currentQuery = '';

// Function to load movies based on query and page
function loadMovies(query, page) {
    console.log(`Searching for: ${query}, Page: ${page}`); // Debugging log
    fetch(`/search?query=${query}&page=${page}`)
        .then(response => response.json())
        .then(data => {
            const resultsContainer = document.getElementById('search-results');
            if (page === 1) {
                resultsContainer.innerHTML = '';
            }
            if (data.length === 0) {
                alert("No more movies found.");
                document.getElementById('load-more').style.display = 'none';
                return;
            }
            data.forEach(movie => {
                const movieElement = document.createElement('div');
                movieElement.innerHTML = `
                    <p></p>
                    <h3>${movie.title} (${movie.year})</h3>
                    <p>${movie.description}</p>
                    <p>ID: ${movie.movie_id}</p>
                    <button onclick="addRecommendation(${movie.movie_id})">Add Recommendation</button>
                `;
                resultsContainer.appendChild(movieElement);
            });
            document.getElementById('load-more').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert("Failed to load movies.");
        });
}


// Event listener for search form submission
document.getElementById('search-form').addEventListener('submit', function(e) {
    e.preventDefault();
    currentQuery = document.getElementById('search-query').value;
    currentPage = 1;
    loadMovies(currentQuery, currentPage);
});

// Event listener for the "Load More" button
document.getElementById('load-more').addEventListener('click', function(e) {
    loadMovies(currentQuery, ++currentPage);
});


// Function to add a recommendation
function addRecommendation(movieId) {
    let jwtToken = getJwtToken(); 
    if (!jwtToken) {
        alert("You are not logged in.");
        return; 
    }

    fetch('/add_recommendation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + jwtToken
        },
        body: JSON.stringify({ movie_id: movieId })
    })
    .then(response => {
        if (response.ok) {
            alert("Recommendation added!");
            loadRecommendedMovies(); // Reload recommended movies
        } else {
            alert("Failed to add recommendation.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("An error occurred while adding the recommendation.");
    });
}
// Function to load recommended movies
function loadRecommendedMovies() {
    fetch('/recommended_movies')
        .then(response => response.json())
        .then(movies => {
            const container = document.getElementById('recommended-movies');
            container.classList.add('movies-container'); 

            container.innerHTML = '';
            if (movies.length === 0) {
                container.innerHTML = '<p>No recommendations found.</p>';
                return;
            }
            movies.forEach(movie => {
                const movieElement = document.createElement('div');
                movieElement.innerHTML = `
                    <h4>${movie.title}</h4>
                    <p>Recommendations: ${movie.recommendation_count}</p>
                    <p>Description: ${movie.description}</p> <!-- Added description -->
                    <button onclick="addRecommendation(${movie.movie_id})">Recommend</button>
                    <p></p>
                `;
                container.appendChild(movieElement);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            alert("Failed to load recommended movies.");
        });
}



// Initialize the recommended movies list on page load
loadRecommendedMovies();
