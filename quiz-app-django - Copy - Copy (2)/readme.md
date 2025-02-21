# QuizLit - Online Quiz Platform

## Overview

QuizLit is an interactive online quiz platform designed to provide users with an engaging learning experience through quizzes. Built with Django, QuizLit allows users to take quizzes, track their performance, and compete on leaderboards. The platform supports role-based access control, ensuring different levels of control for Admins, Managers, and Users.

## Key Features

- Quiz Management: Create, edit, and delete quizzes with multiple formats (MCQs, True/False, Timed Quizzes).
- User Authentication: Secure login and role-based access control.
- Subscription System: Free and premium plans with payment integration via Chapa.
- Performance Tracking: Leaderboards, analytics, and progress tracking.
- Security Measures: Encrypted data storage, role-based permissions, and secure transactions.

## Technology Stack

- Backend: Django (Python)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- Data Visualization: Matplotlib (Python)
- Payment Integration: Chapa

## Project Structure

The project is structured into multiple Django apps, each handling specific functionalities:

- home: Core app for quiz management, user interaction, and performance tracking.
- management: Admin panel for managing quizzes, users, and viewing statistics.
- quiz_project: Root project folder containing global settings, URL configurations, and deployment settings.

## Database Schema

The database schema includes models for User, Quiz, Question, Answer, QuizResult, Category, Subscription, Statistics, and Payment. These models are designed to handle user data, quiz content, performance tracking, and subscription management.

## Setup and Installation

1. Clone the Repository:
   git clone https://github.com/yourusername/quizlit.git
   cd quizlit

2. Create and Activate a Virtual Environment:

   - For Windows:
     python -m venv venv
     venv\Scripts\activate
   - For Mac/Linux:
     python3 -m venv venv
     source venv/bin/activate

3. Install Dependencies:
   pip install -r requirements.txt

4. Database Setup:
   python manage.py migrate

5. Collect Static Files:
   python manage.py collectstatic

6. Run the Development Server:
   python manage.py runserver

   The server will be accessible at http://127.0.0.1:8000/.

## User Guide

1. Registration and Login: Users can register and log in to access quizzes and track their performance.
2. Taking a Quiz: Users can browse quizzes, answer questions, and submit their answers.
3. Viewing Results: After completing a quiz, users can view detailed results, including their score and correct answers.
4. Subscription: Users can subscribe to the Yearly Subscription plan to access premium features.
5. Performance Tracking: Users can view their quiz history, average scores, and performance trends on their dashboard.

## Future Enhancements

- Additional Question Types: Support for True/False, Fill-in-the-Blank, and multimedia-based questions.
- User Gamification: Achievements, badges, and leaderboards to increase engagement.
- User Profile Customization: Personalized profiles and social features.
- Enhanced Payment Options: Multi-currency support and additional payment gateways.
- Advanced Analytics: Detailed performance analytics for admins and AI-driven insights for users.
- Mobile Application: Native mobile apps for iOS and Android with push notifications.
- Enhanced Security: Two-factor authentication and end-to-end encryption.
- Multilingual Support: Localization and region-specific content.
- AI-Powered Content Creation: AI-driven question generation and dynamic quiz difficulty.

## Conclusion

QuizLit is a robust and scalable online quiz platform designed to enhance the learning experience through interactive quizzes, performance tracking, and gamification. With a focus on user experience, security, and future growth, QuizLit is well-positioned to become a leading platform in the online quiz space.

---

For more details, refer to the full documentation in the project repository.
