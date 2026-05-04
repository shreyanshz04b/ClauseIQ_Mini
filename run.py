from app import create_app

# Create Flask application
app = create_app()

if __name__ == "__main__":
    # Start the server
    # host="0.0.0.0" means listen on all network interfaces
    # port=5001 is the port number
    app.run(host="0.0.0.0", port=5001)
