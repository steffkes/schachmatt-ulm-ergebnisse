import streamlit as st
import pandas as pd
import altair as alt
import itertools
import requests

st.set_page_config(layout="wide", page_title="Schachmatt Ulm")
st.title("Schachmatt Ulm")

fieldNames = [
    "Startnummer",
    "_platz",
    "_bib",
    "Name",
    "Team",
    "qualified",
    "Zeit",
    "_differenz",
]


def dataMapperQuali(row):
    return map(lambda entry: dict(zip(fieldNames, entry)), row)


def dataMapperRunde(row):
    [black, white] = row
    black = dict(zip(fieldNames, black))
    white = dict(zip(fieldNames, white))

    return [
        {**black, "Gegner": white["Startnummer"]},
        {**white, "Gegner": black["Startnummer"]},
    ]


def helper(runde, selector):
    r = requests.get(
        "https://my3.raceresult.com/313906/RRPublish/data/list",
        params={
            "key": "5af851eb0259b1c543aeba7da178780e",
            "listname": "01 - Online|Results",
            "page": "results",
            "contest": 1,
            "selectorResult": selector,
        },
    )

    df = pd.json_normalize(
        list(
            itertools.chain.from_iterable(
                map(
                    dataMapperQuali if runde == "Q" else dataMapperRunde,
                    r.json()["data"].values(),
                )
            )
        )
    )
    df["qualified"] = df["qualified"] == "Q"
    df["Runde"] = runde

    return df


df = pd.concat(
    [
        helper(runde, selector)
        for (runde, selector) in [
            ("Q", 1),
            ("1", 2),
            ("2", 3),
            ("3", 4),
            ("4", 5),
            ("5", 6),
            ("6", 7),
            ("7", 8),
            ("7", 9),
        ]
    ]
)


def teamHelper(row):
    return (row["Startnummer"], "#{Startnummer}: {Name} ({Team})".format(**row))


teams = dict(
    teamHelper(row)
    for (_index, row) in df[["Startnummer", "Name", "Team"]]
    .drop_duplicates()
    .iterrows()
)

selected_team = st.selectbox(
    "Für welches Team möchtest du die Ergebnisse sehen?",
    sorted(df["Startnummer"].unique().tolist()),
    format_func=lambda team: teams[team],
)

roundsList = ["Q", "1", "2", "3", "4", "5", "6", "7"]

st.altair_chart(
    alt.layer(
        alt.Chart(df)
        .mark_point()
        .transform_filter(alt.FieldEqualPredicate(field="Gegner", equal=selected_team))
        .encode(
            x=alt.X("Runde:O"),
            y=alt.Y("Zeit"),
            color=alt.Color("qualified", legend=None).scale(range=["#080", "#f00"]),
        ),
        alt.Chart(df)
        .mark_line(color="black")
        .transform_filter(
            alt.FieldEqualPredicate(field="Startnummer", equal=selected_team)
        )
        .encode(
            x=alt.X("Runde:O").axis(labelAngle=0).scale(domain=roundsList),
            y=alt.Y("Zeit").scale(reverse=True),
        ),
    ),
    use_container_width=True,
)

if st.checkbox("Rohdaten anzeigen?"):
    st.write(df)
