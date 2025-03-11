from app import create_app, db, models
app = create_app()
app.debug = True
app.config['SQLALCHEMY_RECORD_QUERIES'] = True

if __name__ == '__main__':
    app.run(debug=True)
