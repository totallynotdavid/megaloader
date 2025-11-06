# Megaloader Demo Website

Django-based web interface for the Megaloader library.

## Features

- Web-based URL submission form
- Real-time download status
- Display of supported platforms
- Simple and clean UI

## Setup

1. Install dependencies:

```bash
cd demo
uv pip install -e .
```

2. Run migrations:

```bash
python manage.py migrate
```

3. Start the development server:

```bash
python manage.py runserver
```

4. Open your browser to `http://localhost:8000`

## Usage

1. Enter a URL from any supported platform
2. Configure download options (subdirectories, proxy)
3. Click "Download" to start the download
4. Files will be saved to the `downloads/` directory

## Development

The demo uses:
- Django 5.1 for the web framework
- SQLite for the database (can be changed in settings)
- Megaloader core library for download functionality

### Project Structure

```
demo/
├── config/           # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── downloader/       # Main app
│   ├── views.py
│   ├── urls.py
│   └── models.py
├── templates/        # HTML templates
├── static/          # Static files (CSS, JS)
└── manage.py        # Django management script
```

## Future Enhancements

- Download queue management
- User authentication
- Download history tracking
- Progress tracking with WebSockets
- Batch URL processing
- API endpoints
