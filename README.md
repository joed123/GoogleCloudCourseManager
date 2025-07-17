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
