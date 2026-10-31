import streamlit as st
from snowflake.snowpark.functions import col
import requests

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Page title
st.title("🥤 Customize Your Smoothie! 🥤")
st.write("Choose the fruits you want in your custom smoothie!")

# Name on order
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Get fruit options from Snowflake
my_dataframe = session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")

# Create a lookup between fruit names and API search names
fruit_lookup = {
    row["FRUIT_NAME"]: row["SEARCH_ON"]
    for row in my_dataframe.select("FRUIT_NAME", "SEARCH_ON").collect()
}

# Get fruit names for the dropdown
fruit_names = my_dataframe.select(col("FRUIT_NAME")).to_pandas()["FRUIT_NAME"].tolist()

# Allow customers to select multiple fruits
selected_fruits = st.multiselect(
    "What fruits would you like in your smoothie?",
    fruit_names
)

# Process smoothie order
if selected_fruits:
    ingredients_string = ""

    for fruit_chosen in selected_fruits:
        # Add fruit to the order
        ingredients_string += fruit_chosen + " "

        # Get the API search name from Snowflake
        fruit_for_api = fruit_lookup[fruit_chosen]

        # Get nutrition information for this fruit
        smoothiefroot_response = requests.get(
            "https://my.smoothiefroot.com/api/fruit/" + fruit_for_api,
            timeout=15
        )

        # Display nutrition information
        if smoothiefroot_response.ok:
            st.dataframe(
                data=smoothiefroot_response.json(),
                use_container_width=True
            )
        else:
            st.warning(
                f"Nutrition information is unavailable for {fruit_chosen}."
            )

    # Display selected ingredients once
    st.write(ingredients_string)

    # Create SQL insert statement
    my_insert_stmt = """
        INSERT INTO SMOOTHIES.PUBLIC.ORDERS
        (INGREDIENTS, NAME_ON_ORDER)
        VALUES (?, ?)
    """

    # Submit button
    time_to_insert = st.button("Submit Order")

    if time_to_insert:
        session.sql(
            my_insert_stmt,
            params=[ingredients_string, name_on_order]
        ).collect()

        st.success("Your Smoothie is ordered!", icon="✅")


