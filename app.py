from shiny.express import input, render, ui

from location import location

loc = location("loc", "Where do you live? (City or region)")


@render.express
def out():
    location = loc()
    if location is not None:
        lat, long = location
        f"{lat:.6f}, {long:.6f}"
