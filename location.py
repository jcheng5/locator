from __future__ import annotations

import json
import os

import ipyleaflet as L
from dotenv import load_dotenv
from openai import AsyncOpenAI
from shiny import Inputs, Outputs, Session, reactive, req
from shiny.express import module, render, ui
from shinywidgets import reactive_read, render_widget

load_dotenv()
if os.getenv("OPENAI_API_KEY") is None:
    raise RuntimeError("$OPENAI_API_KEY was not found")

client = AsyncOpenAI()


@module
def location(
    input: Inputs,
    output: Outputs,
    session: Session,
    label: str | None,
    **kwargs,
):
    ui.input_text("loc_text", label, **kwargs)
    ui.input_task_button("lookup", "Lookup")

    @reactive.effect
    @reactive.event(input.lookup)
    def geocode():
        geocode_task.invoke(input.loc_text())

    @ui.bind_task_button(button_id="lookup")
    @reactive.extended_task
    async def geocode_task(loc_text: str) -> tuple[float, float] | None:
        response = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You'll be given a geographic location; "
                    "return a JSON object of the latitude/longitude of "
                    "the location, using the keys 'lat' and 'long'.",
                },
                {"role": "user", "content": loc_text},
            ],
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
        )
        try:
            parsed_result = json.loads(response.choices[0].message.content)
            return parsed_result["lat"], parsed_result["long"]
        except Exception as e:
            print(response.choices[0].message)
            return None, None

    @render.express
    def location_preview():
        loc = geocode_task.result()
        if loc is not None:
            ui.p(
                "Drag around the marker if that doesn't look right. (It doesn't need to be exact.) Or try another lookup."
            )

            @render_widget
            def location_map():
                map = L.Map(center=loc, zoom=8, scoll_wheel_zoom=True)
                map.layout.width = "400px"
                map.layout.height = "300px"
                marker = L.Marker(location=loc)
                map.add_layer(marker)

                @reactive.effect
                def sync_marker():
                    marker_loc.set(reactive_read(marker, "location"))

                return map

    marker_loc = reactive.value(None)

    return marker_loc
