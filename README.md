### data-representation-project

#### Author
Daria Sep (G00411221@atu.ie)
#### Course Details
Course: Higher Diploma in Computing in Data Analytics

Module: Data Representation

### Description
This repository is a submission of the Project for the Data Representation module. 

The project objective: Write a program that demonstrates understanding of creating and consuming RESTful APIs: Create a basic Flask server that has a
- REST API, (to perform CRUD operations)
- One database table and
- Accompanying web interface, using AJAX calls, to perform these CRUD operations

### Movie Recommendations App

The Movie Recommendations App is a web-based movie recommendation platform. It allows users to search for movies, view details about these movies, and add them to a recommendation list. Key functionalities include:

- **User Authentication**: The app supports user registration and login, utilizing JWT (JSON Web Tokens) for secure authentication. Registered users can log in to access protected routes and features.

- **Movie Search**: Users can search for movies using the TMDB (The Movie Database) API. The search functionality retrieves movie information like title, release year, and description based on user queries.

- **Adding Recommendations**: Authenticated users can add movies to their recommendation list. This feature inserts the movie details into a local database and keeps track of the number of recommendations each movie receives.

- **Displaying Recommended Movies**: The application provides a list of recommended movies, showcasing their titles, the number of times they've been recommended, and a brief description.

- **Database Integration**: The application uses a MySQL database to store user data, movie details, and recommendation counts. It includes database connection management and SQL queries for data retrieval and updates.

- **Web Interface**: The Flask app serves web pages that allow users to interact with these features through a browser, offering a user-friendly interface for movie searching and recommendation management.
