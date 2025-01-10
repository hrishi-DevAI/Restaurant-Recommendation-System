from flask import Flask, request, render_template, jsonify
import pandas as pd
import pickle
import folium

# Initialize the Flask app
app = Flask(__name__)

# Load pre-trained models and data
lasvegas_df = pd.read_csv('data/lasvegas.csv')
with open('models/review_scaler.pkl', 'rb') as f:
    review_scaler = pickle.load(f)
with open('models/location_model.pkl', 'rb') as f:
    location_model = pickle.load(f)
with open('models/review_model.pkl', 'rb') as f:
    review_model = pickle.load(f)

# Home route
@app.route('/')
def home():
    return render_template('index.html')  # Create an HTML form for user input

# Recommendation route
@app.route('/recommend', methods=['POST'])
def recommend():
    # Get user input from form
    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])
    stars = float(request.form['stars'])
    reviews = int(request.form.get('reviews', 100))  # Default to 100

    # Step 1: Predict location cluster
    user_location = [[longitude, latitude]]
    location_cluster = location_model.predict(user_location)[0]

    # Step 2: Scale the review count
    scaled_reviews = review_scaler.transform([[reviews]])[0][0]

    # Step 3: Predict review cluster
    review_features = [[stars, scaled_reviews]]
    review_cluster = review_model.predict(review_features)[0]

    # Step 4: Filter recommendations
    filtered_restaurants = lasvegas_df[
        (lasvegas_df['cluster'] == location_cluster) &
        (lasvegas_df['Review_categories'] == review_cluster)
    ]

    # Step 5: Sort and select top recommendations
    recommendations = filtered_restaurants.sort_values(
        by=['stars', 'review_count'], ascending=False
    ).head(10)

    # Step 6: Create a map with recommendations
    map_center = [latitude, longitude]
    restaurant_map = folium.Map(location=map_center, zoom_start=12)

    # Add user location
    folium.Marker(
        location=map_center,
        popup="Your Location",
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(restaurant_map)

    # Add restaurant markers
    for _, row in recommendations.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['name']}<br>Stars: {row['stars']}<br>Reviews: {row['review_count']}",
            icon=folium.Icon(color='green', icon='cutlery')
        ).add_to(restaurant_map)

    # Convert map to HTML
    map_html = restaurant_map._repr_html_()

    # Return recommendations and map
    return render_template('results.html', recommendations=recommendations, map_html=map_html)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)