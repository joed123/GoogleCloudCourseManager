# Tarpaulin API

A lightweight course management REST API built as an alternative to Canvas. This application provides comprehensive functionality for managing users, courses, and student enrollment with secure authentication.

## Features

- **User Management**: Admin, instructor, and student roles with secure JWT authentication
- **Course Management**: Complete CRUD operations for courses with proper authorization
- **Student Enrollment**: Flexible enrollment/disenrollment system
- **Avatar Management**: File upload/download functionality with Google Cloud Storage
- **RESTful Design**: Clean, well-structured API following REST principles

## Technology Stack

- **Backend**: Python 3, Flask
- **Database**: Google Cloud Datastore
- **Authentication**: Auth0 with JWT tokens
- **File Storage**: Google Cloud Storage
- **Deployment**: Google App Engine

## Security Features

- JWT token validation for protected endpoints
- Role-based access control
- Secure file handling with Google Cloud Storage
- Input validation and sanitization
- Proper error handling without information leakage

## Development Notes

- The application uses Google Cloud Datastore for data persistence
- All sensitive configuration is managed through environment variables
- The API follows RESTful principles with appropriate HTTP methods and status codes


## API Endpoints

### Authentication

#### User Login
```
POST /users/login
```
Generate a JWT token for authentication.

**Request Body:**
```json
{
  "username": "admin@osu.com",
  "password": "Cheese1234!"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### User Management

#### Get All Users
```
GET /users
```
**Protection:** Admin only

Returns summary information of all users (id, role, sub).

**Response (200):**
```json
[
  {
    "id": 5631671361601536,
    "role": "student",
    "sub": "auth0|664384d7829d72375c7a034d"
  },
  {
    "id": 5632499082330112,
    "role": "instructor",
    "sub": "auth0|664383f2ad88a0630023ab9b"
  }
]
```

#### Get User Details
```
GET /users/:user_id
```
**Protection:** Admin or user with matching JWT

Returns detailed user information including avatar URL (if exists) and courses for instructors/students.

**Response (200) - Instructor with avatar:**
```json
{
  "avatar_url": "http://localhost:8080/users/5644004762845184/avatar",
  "courses": [
    "http://localhost:8080/courses/5744039651442688",
    "http://localhost:8080/courses/5759318150348800"
  ],
  "id": 5644004762845184,
  "role": "instructor",
  "sub": "auth0|6583ae12895d09a70ba1c7c5"
}
```

---

### Avatar Management

#### Upload/Update Avatar
```
POST /users/:user_id/avatar
```
**Protection:** User with matching JWT
**Content-Type:** multipart/form-data

Upload a PNG file as the user's avatar to Google Cloud Storage.

**Request Body:**
- Form-data with key "file" containing the PNG image

**Response (200):**
```json
{
  "avatar_url": "http://localhost:8080/users/5644004762845184/avatar"
}
```

#### Get User Avatar
```
GET /users/:user_id/avatar
```
**Protection:** User with matching JWT

Returns the avatar image file from Google Cloud Storage.

#### Delete User Avatar
```
DELETE /users/:user_id/avatar
```
**Protection:** User with matching JWT

Deletes the avatar file from Google Cloud Storage.

**Response:** 204 No Content

---

### Course Management

#### Create Course
```
POST /courses
```
**Protection:** Admin only

**Request Body:**
```json
{
  "subject": "CS",
  "number": 493,
  "title": "Cloud Application Development",
  "term": "fall-24",
  "instructor_id": 5644004762845184
}
```

**Response (201):**
```json
{
  "id": 5710353417633792,
  "instructor_id": 5644004762845184,
  "number": 493,
  "self": "http://localhost:8080/courses/5710353417633792",
  "subject": "CS",
  "term": "fall-24",
  "title": "Cloud Application Development"
}
```

#### Get All Courses (Paginated)
```
GET /courses
GET /courses?offset=3&limit=3
```
**Protection:** Unprotected

Returns paginated list of courses (page size: 3), sorted by subject.

**Response (200):**
```json
{
  "courses": [
    {
      "id": 5633378543992832,
      "instructor_id": 5644004762845184,
      "number": 493,
      "self": "http://localhost:8080/courses/5633378543992832",
      "subject": "CS",
      "term": "fall-24",
      "title": "Cloud Application Development"
    }
  ],
  "next": "http://localhost:8080/courses?limit=3&offset=3"
}
```

#### Get Course Details
```
GET /courses/:course_id
```
**Protection:** Unprotected

Returns detailed information about a specific course (without enrollment data).

#### Update Course
```
PATCH /courses/:course_id
```
**Protection:** Admin only

Partial update of course properties.

**Request Body (example):**
```json
{
  "instructor_id": 5644004762845184
}
```

#### Delete Course
```
DELETE /courses/:course_id
```
**Protection:** Admin only

Deletes the course and all associated enrollment data.

**Response:** 204 No Content

---

### Enrollment Management

#### Update Course Enrollment
```
PATCH /courses/:course_id/students
```
**Protection:** Admin or course instructor

Add or remove students from a course.

**Request Body:**
```json
{
  "add": [
    5642368648740864,
    5714489739575296
  ],
  "remove": [
    5636645067948032
  ]
}
```

**Response:** 200 OK (empty body)

#### Get Course Enrollment
```
GET /courses/:course_id/students
```
**Protection:** Admin or course instructor

Returns list of student IDs enrolled in the course.

**Response (200):**
```json
[
  5646488461901824,
  5631671361601536,
  5642368648740864
]
```

---

## Error Responses

All endpoints return consistent error messages for common HTTP status codes:

| Status Code | Error Message |
|-------------|---------------|
| 400 | `{"Error": "The request body is invalid"}` |
| 401 | `{"Error": "Unauthorized"}` |
| 403 | `{"Error": "You don't have permission on this resource"}` |
| 404 | `{"Error": "Not found"}` |
| 409 | `{"Error": "Enrollment data is invalid"}` |


