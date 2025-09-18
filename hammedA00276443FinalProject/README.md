# Portfolio Website

This repository contains the source code for my personal portfolio website. This website showcases my projects, skills, and provides a way for visitors to contact me.

## Features

*   **Home Page**: A welcoming introduction with a brief summary of my skills and passion.
*   **About Page**: Detailed information about my background, experience, and technical skills.
*   **Portfolio Page**: A gallery of my projects with descriptions and links.
*   **Contact Page**: A form for visitors to send me messages, which are then stored in a CSV file.
*   **Responsive Design**: The website is designed to work on various devices, including desktops, tablets, and mobile phones.
*   **Animations**: Smooth animations using ScrollReveal and Typed.js to enhance user experience.

## Technologies Used

### Frontend

*   **HTML5**
*   **CSS3**
*   **JavaScript**
*   [Font Awesome](https://fontawesome.com/) for icons.
*   [Typed.js](https://github.com/mattboldt/typed.js) for the typing animation.
*   [ScrollReveal](https://scrollrevealjs.org/) for scroll animations.

### Backend

*   **Python**
*   **Flask**: A lightweight WSGI web application framework.

## Setup and Installation

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

## File Structure

```
hammedA00276443FinalProject/
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

## Contributing

Contributions are welcome! If you have any suggestions or find any bugs, please open an issue or create a pull request.

## License

This project is licensed under the MIT License.