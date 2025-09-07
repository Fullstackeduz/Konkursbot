# Telegram Contest Bot

## Overview

This is a Telegram bot designed for running contests and managing user engagement through mandatory channel subscriptions. The bot features user registration with phone number verification, referral system with point rewards, admin panel for comprehensive management, and subscription verification for contest participation. Built with the aiogram framework for asynchronous Telegram bot operations, it includes SQLite database for data persistence and comprehensive user analytics.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
- **Bot Framework**: aiogram v3 with async/await pattern for handling Telegram API interactions
- **State Management**: Finite State Machine (FSM) using aiogram's built-in FSM with memory storage for managing conversation flows
- **Routing**: Modular router system separating user handlers from admin handlers

### Database Design
- **Database**: SQLite with custom Database class providing thread-safe operations
- **Schema**: Normalized tables for users, admins, mandatory subscriptions, transactions, referrals, and bot statistics
- **Data Integrity**: Primary key relationships and foreign key constraints for referral tracking

### Authentication & Authorization
- **User Registration**: Two-step process requiring channel subscription verification and phone number validation
- **Admin System**: Role-based access control with configurable admin IDs and permission levels
- **Subscription Verification**: Real-time API calls to verify user membership in mandatory channels

### User Management
- **Registration Flow**: Multi-state process with subscription checking, phone validation (+998 format), and automatic point allocation
- **Referral System**: Automatic referrer detection and reward distribution with database tracking
- **User Analytics**: Comprehensive activity tracking including registration dates, last activity, and engagement metrics

### Admin Panel Architecture
- **Modular Design**: Separate admin router with dedicated state management for administrative functions
- **User Management**: Bulk operations, user search, activity monitoring, and manual user management
- **Broadcasting**: Mass messaging capabilities with error handling and delivery tracking
- **Statistics Dashboard**: Real-time analytics with exportable reports and historical data visualization
- **Content Management**: Dynamic text editing system for bot messages and contest information

### Statistics & Analytics
- **StatsManager**: Dedicated class for analytics with support for daily, weekly, monthly, and all-time statistics
- **Data Export**: Pandas integration for Excel export functionality with pagination for large datasets
- **Performance Metrics**: User growth tracking, engagement analytics, and referral performance monitoring

### Error Handling & Logging
- **Comprehensive Logging**: Multi-level logging with file and console output for debugging and monitoring
- **Exception Handling**: Graceful error handling for Telegram API errors and database operations
- **Validation**: Input validation for phone numbers, user permissions, and subscription status

## External Dependencies

### Telegram Integration
- **Telegram Bot API**: Full integration through aiogram framework for message handling, callback queries, and user management
- **Channel Management**: API calls for subscription verification and member status checking

### Data Management
- **SQLite**: Embedded database for local data persistence without external server requirements
- **Pandas**: Data manipulation and Excel export functionality for analytics and reporting

### Development Tools
- **asyncio**: Asynchronous programming support for concurrent operations
- **logging**: Built-in Python logging for application monitoring and debugging
- **os/sys**: Environment variable management and system integration