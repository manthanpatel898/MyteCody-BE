from src.app.app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    # Run the Flask application
    app.run(debug=True)
