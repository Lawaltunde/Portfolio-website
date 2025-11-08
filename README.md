# Hammed Lawal's Portfolio Website

Welcome to the repository for my personal portfolio website! This site is a living showcase of my journey in software engineering and data analysis, featuring projects I've built, skills I've honed, and a little bit about who I am.

## 🚀 Features

*   **Home Page**: A welcoming introduction with a brief summary of my skills and passion.
*   **About Page**: A deeper dive into my background, professional experience, and the technologies I work with.
*   **Contact Page**: A functional contact form that allows visitors to get in touch with me directly.
*   **Responsive Design**: The website is fully responsive, providing an optimal viewing experience across desktops, tablets, and mobile devices.
## 🛠️ Tech Stack

<p align="left">
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=html,css,javascript,python,flask" />
  </a>
</p>


*   **HTML5**
*   **CSS3**
*   **JavaScript**
*   [Font Awesome](https://fontawesome.com/) for icons.
*   [Typed.js](https://github.com/mattboldt/typed.js) for the typing animation.
*   [ScrollReveal](https://scrollrevealjs.org/) for scroll animations.

### Backend

*   **Python**
*   **Flask**: A lightweight WSGI web application framework.

## 📦 Setup and Installation

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Lawaltunde/Portfolio-website.git
    cd Portfolio-website/hammedA00276443FinalProject
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python app.py
    ```

5.  Open your browser and navigate to `http://127.0.0.1:5000`.

## � Configuration

- DATA_BACKEND: Choose the data store. Options: `supabase` or `sqlite`.
    - If not set, the app auto-selects `supabase` when `SUPABASE_URL` and `SUPABASE_KEY` are present; otherwise `sqlite`.
    - In production, set `DATA_BACKEND=supabase` and provide Supabase env vars.
- SUPABASE_URL, SUPABASE_KEY (or NEXT_PUBLIC_* fallbacks): Required for Supabase mode.
- SUPABASE_SERVICE_ROLE_KEY: Optional; used only for one-off migrations via `migrate_to_supabase.py`.

## ☁️ Deploying to Render or Vercel

- Render (recommended for Flask):
    - Build command: `pip install -r requirements.txt`
    - Start command: `gunicorn --chdir . wsgi:app`
    - Environment: `DATA_BACKEND=supabase`, plus Supabase envs and `SECRET_KEY`.
- Vercel:
    - Use Vercel’s Python/Flask template or `vercel-python-wsgi`. Configure `wsgi.py` as the entry point.
    - Set the same environment variables as above.

In production, the app will not fallback to SQLite when `DATA_BACKEND=supabase` is set—writes will fail fast if Supabase is unavailable.

## 📂 File Structure

```
portfolio/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/
│   ├── fontawesome-free-6.2.1-web/
│   ├── images/
│   ├── script.js           # JavaScript for animations and interactivity
│   └── style.css           # Main stylesheet
└── templates/
    ├── about.html          # About page
    ├── contact.html        # Contact page
    ├── error404.html       # 404 error page
    ├── index.html          # Home page
    ├── portfolio.html      # Portfolio page
    └── thank_you.html      # Thank you page after form submission
```

## 🤝 Contributing

I'm always open to collaboration and suggestions! If you have any ideas for improvement or find any bugs, please feel free to open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License.