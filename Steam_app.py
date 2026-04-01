import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import kagglehub
import streamlit as st
import os

############################## Functions ##############################
def format_range(label):
    parts = label.split(" - ")
    start = int(parts[0])
    end = int(parts[1])
    
    def short(n):
        if n >= 1_000_000:
            return f"{n//1_000_000}M"
        elif n >= 1_000:
            return f"{n//1_000}K"
        else:
            return str(n)
    
    return f"{short(start)} - {short(end)}"

def platform_type(row):
    platforms = []
    if row["Windows"]:
        platforms.append("Windows")
    if row["Mac"]:
        platforms.append("Mac")
    if row["Linux"]:
        platforms.append("Linux")

    if len(platforms) == 1:
        return platforms[0] + " Only"
    elif len(platforms) > 1:
        return "Multi-platform"
    else:
        return "None"
    
def price_category(price):
    if price == 0:
        return "Free"
    elif price < 10 :
        return "Low"
    elif price < 30:
        return "Mid"
    else:
        return "High"

def extract_midpoint(label):
    start, end = map(int, label.split(" - "))
    return (start + end) / 2

def lighten_color(hex_color, factor):
    """Renvoie une nuance plus claire du hex_color"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    r = min(int(r + (255 - r) * factor), 255)
    g = min(int(g + (255 - g) * factor), 255)
    b = min(int(b + (255 - b) * factor), 255)
    
    return f'#{r:02x}{g:02x}{b:02x}'
############################## /Functions ############################## 

######################## Setup ##############################
path = kagglehub.dataset_download("fronkongames/steam-games-dataset")

df = pd.read_csv(os.path.join(path, "games.csv"))

df.columns = ['Name', 'Release date', 'Estimated owners', 'Peak CCU',
       'Required age', 'Price', 'Discount', 'DLC count', 'About the game',
       'Supported languages', 'Full audio languages', 'Reviews',
       'Header image', 'Website', 'Support url', 'Support email', 'Windows',
       'Mac', 'Linux', 'Metacritic score', 'Metacritic url', 'User score',
       'Positive', 'Negative', 'Score rank', 'Achievements', 'Recommendations',
       'Notes', 'Average playtime forever', 'Average playtime two weeks',
       'Median playtime forever', 'Median playtime two weeks', 'Developers',
       'Publishers', 'Categories', 'Genres', 'Tags', 'Screenshots', 'Movies']

    # Couleur de base (bleu)
base_color = "#064979"

######################## /Setup ##############################

pd.set_option('display.max_columns', None)

### Remove the games that had 0 estimated owners ###
df = df[df['Estimated owners'] != '0 - 0']
### /Remove the games that had 0 estimated owners ###

                    ### Playtime vs Sales ###
owners_counts = (df["Estimated owners"].value_counts().reset_index())
owners_counts.columns = ["Estimated owners", 'Number of games']

owners_counts["Estimated owners"] = owners_counts["Estimated owners"].apply(format_range)

df_playtime = df[df["Average playtime forever"] > 0]
df_playtime = df_playtime[df_playtime["Average playtime forever"] < 50000]
df_playtime["Price Category"] = df_playtime["Price"].apply(price_category)
                    ### /Playtime vs Sales ###

                    ### Platform type ###
df["Platform Type"] = df.apply(platform_type, axis = 1)   
# Count of platform types and number of games per platform
platform_type_counts = df["Platform Type"].value_counts().reset_index()
platform_type_counts.columns = ["Platform Type", "Number of Games"]
                    
# Nombre de parts
n = len(platform_type_counts)
# Créer une liste de nuances
colors = [lighten_color(base_color, i/(n-1)*0.6) for i in range(n)]  # 0 à 60% plus clair
                    ### /Platform type ###

                    ### Reviews ###
df_reviews = df.melt(
    id_vars=["Estimated owners"],
    value_vars=["Positive", "Negative"],
    var_name="Review Type",
    value_name="Review Count"
)

order = [
    "0 - 20K",
    "20K - 50K",
    "50K - 100K",
    "100K - 200K",
    "200K - 500K",
    "500K - 1M",
    "1M - 2M",
    "2M - 5M",
    "5M - 10M",
    "10M - 20M",
    "20M - 50M",
    "50M - 100M",
    "100M - 200M",]

df_reviews["Estimated owners"] = df_reviews["Estimated owners"].apply(format_range)
                    ### /Reviews ###

                    ### Release ###
df["Release Year"] = pd.to_datetime(df["Release date"], errors="coerce").dt.year
df_year = df[df["Release Year"].notna()]

games_per_year = (
    df_year["Release Year"]
    .value_counts()
    .sort_index()
    .reset_index()
)
games_per_year.columns = ["Release Year", "Number of Games"]
                    ### /Release ###

                    ### Sales per price ###
df_sales = df
df_sales["Price Category"] = df_sales["Price"].apply(price_category)

df_sales =df_sales[["Estimated owners", "Price Category"]].copy()
df_sales["Estimated owners"] = df_sales["Estimated owners"].apply(format_range)

df_sales["Estimated owners"] = pd.Categorical(
    df_sales["Estimated owners"],
    categories=order,
    ordered=True)
                    ### /Sales per price ###

                    ### Publishers ###
publisher_df = df[["Publishers", "Estimated owners"]].copy()
publisher_df["Estimated owners"] = publisher_df["Estimated owners"].apply(extract_midpoint)

publisher_df = publisher_df.groupby("Publishers", as_index = False)["Estimated owners"].sum()
publisher_df = publisher_df.sort_values(by= "Estimated owners" ,ascending= False)
                    ### /Publishers ###

###################################### /Code #################################################

###################################### Charts ################################################
salesPage, priceCatPage, publiPage, solutionPage = st.tabs(["Ventes", "Catégories de prix", "État général", "Solution proposée"])

                ### Bar chart for sales by estimated owners ###
with salesPage:
    containerSales01 = st.container(border = False)
    containerSales02 = st.container(border= False, horizontal = True,)
    containerSales03 = st.container(border = False)
    
    with containerSales01:
        st.title(body = "Étude des ventes sur Steam en terme de volume", width = "content", text_alignment="left")

        play_sales_barChart = px.bar(
            x=owners_counts["Number of games"],
            y=owners_counts["Estimated owners"],
            orientation="h",
            text=owners_counts["Number of games"],
        )
        play_sales_barChart.update_traces(marker_color="#064979")

        st.markdown("<p style='font-size: 30px;'> La plupart des jeux sur Steam n'atteignent pas les 20K acheteurs</p>", 
                    width = "content", text_alignment= "left", unsafe_allow_html=True)
        play_sales_barChart.update_layout(
            template = "plotly_dark",
            xaxis_title="Jeux",
            yaxis_title="Estimation d'acheteurs",
            height = 750,
            yaxis_showgrid=False,
            xaxis=dict(
                showgrid=False,
                showticklabels=False,
                showline=False,
                zeroline=False
                    ),
            yaxis=dict(
                showgrid=False,
                ticklabelstandoff=10
            ),
        )

        # Add annotation highlighting the key insight
        play_sales_barChart.add_annotation(
            x=74500,
            y="20K - 50K",
            yshift=-25,
            text="Plus de 75% des jeux ont moins de 20K d'acheteurs",
            showarrow=True,
            arrowhead=5
        )

        play_sales_barChart.add_annotation(
            x = 0.5,
            y = 2.5,
            xref = "paper",
            yref = "y",
            text = " +100K acheteurs ",
            showarrow= False,
            font = dict(size=13, color = "#555"),
            bgcolor="white"
        )

        play_sales_barChart.add_shape(
            type="line",
            x0=0,
            x1=1,
            xref="paper",
            y0=2.5,
            y1= 2.5,
            yref="y",
            line=dict(color="grey", width=1, dash="dot")
        )

        #DISPLAY
        st.plotly_chart(play_sales_barChart)
                ### /Bar chart for sales by estimated owners ###

                ### Pie chart for sales by estimated owners ###
    with containerSales02:
        labels = owners_counts['Estimated owners'].to_string()
        pie = go.Figure(data = [go.Pie(labels = owners_counts['Estimated owners'], 
                               values= owners_counts['Number of games'], 
                               pull = [0.2,0,0,0,0,0,0,0,0,0,0,0,0],
                               marker= dict(colors =colors))],
                               )

        pie.update_layout(
            template = "plotly_dark",
            title = {
                'text': "<span style='font-size:22px'> Proportion d'acheteurs estimés</span style>",
                'x': 0.5,
                'xanchor': 'center'
            })

        #DISPLAY
        st.plotly_chart(pie)
            ### /Pie chart for sales by estimated owners ###

            ### Doughnut for platform repartition ###

        platform = go.Figure(
            data= [go.Pie(labels = platform_type_counts["Platform Type"],
                    values = platform_type_counts["Number of Games"],
                    marker = dict(colors = colors))])

        platform.update_layout(
            template = "plotly_dark",
            title = { 
                'text': "<span style='font-size:15px'>Répartition des jeux par plateformes</span style>"
                "<br>Windows domine largement le marché"
                "<br>des jeux Steam</br>",
                'x': 0.5,
                'xanchor': 'center'
                })

        platform.update_traces(hole = .5)

        st.plotly_chart(platform)
            ### /Doughnut for platform repartition ###
        with containerSales03:
            st.title(body = "Notes")
            st.markdown(body = "Publier son jeu sur Steam n'est plus gage de succès commercial. Le marché est innondé.")
            st.markdown(body = "Windows domine le marché car une forte majorité des jeux mis à la vente sur Steam proviennent des studios indépendants. En terme de production," \
            "c'est moins coûteux de sortir un jeu sur une plateforme que de le faire sur une multitude.")

with priceCatPage:
            ### Playtime vs Price Category ###
    box_plot_colors = [lighten_color(base_color, i/(4)*0.6) for i in range(4)]  # 0 à 60% plus clair
    
    st.title(body = "Les jeux payants ont tendance à avoir un plus grand niveau de rétention que les jeux gratuits")
    
    box_plot = px.box(
        df_playtime,
        x="Price Category",
        y="Average playtime forever",
        color="Price Category",
        points=False,
        category_orders={
            "Price Category": ["Free", "Low", "Mid", "High"]
        },
        color_discrete_sequence= box_plot_colors)

    box_plot.update_layout(
        template="plotly_dark",

        # title={
            #"text": "<span style='color:#ffffff;font-size:26px;'>Les jeux payants ont tendant à avoir un plus grand temps de jeu que les jeux gratuits.</span>"
            #"<br>Meilleure rétention des joueurs pour les jeux payants</br>"},
        showlegend=False,
        height=700,
        xaxis_title=None,
        yaxis_title="Temps de jeu moyen (par heure)",

        yaxis_showgrid=False,
        xaxis_tickangle=0
    )

    # playtime usually has large variation
    box_plot.update_yaxes(
        type="log",
        tickvals=[1,10,100,1000,10000],
        ticktext=["1","10","100","1k","10k"])
    
    st.plotly_chart(box_plot)
            ### /Playtime vs Price Category ###

            ### Sales per price ###
    categories = df_sales["Estimated owners"].cat.categories
    m = len(categories)
    
    estimated_owners_colors = [lighten_color(base_color, i/(m-1)*0.6) for i in range(m)]
    
    st.title(body = "Les jeux qui se vendent le mieux sont les jeux peu coûteux")
    st.markdown(body = "(Entre 0.5€ et 10€)")

    fig_sales = px.histogram(
        df_sales,
        x = "Price Category",
        color = "Estimated owners",
        barmode = "stack",
            category_orders={
        "Price Category": ["Free", "Low", "Mid", "High"]},
        color_discrete_sequence= estimated_owners_colors)

    fig_sales.update_layout(
        template = "plotly_dark",
        # title={
        #     "text": "<span style='font-size:30px'>Les jeux qui se vendent le mieux sont les jeux peu coûteux</span>"
        #         "<br><span style='font-size:16px;color:#ffffff'>(Entre 0.5€ et 10€)</span>",
        #     'x': 0.1},
        xaxis_title="Catégorie de prix des jeux",
        yaxis_title="Estimation d'acheteurs",
        height = 750,
        yaxis_showgrid=False,
    )

    st.plotly_chart(fig_sales)

    st.title("Notes")
    st.markdown("Contrairement à une idée reçue, les jeux gratuits (ou freemium) ne rencontrent pas un succès supérieur à celui des jeux au faible coût. " \
    "Les jeux ayant un prix élevé ont un meilleur taux de rétention mais est-ce dû à l'engagement du joueur par rapport à la dépense ou est-ce un gage de qualité" \
    "du jeu ?")
            ### /Sales per price ###

with publiPage:
            ### Publishers ###
    publi_colors = [lighten_color(base_color, i/(5)*0.6) for i in range(5)]  # 0 à 60% plus clair
    
    publi_bar = px.bar(
        publisher_df.head(),
        x="Publishers",
        y="Estimated owners",
        color = "Publishers",
        color_discrete_sequence= publi_colors
    )

    publi_bar.update_layout(
        template = "plotly_dark",
        title={
            "text": "<span style='font-size:30px'>Les éditeurs vendant le mieux sur Steam</span>",
            'x': 0.1,  # center
            },
    )

    st.plotly_chart(publi_bar)
            ### /Publishers ###

            ### Reviews ###
    reviews_box_plot = px.box(
        df_reviews,
        x="Estimated owners",
        y="Review Count",
        color="Review Type",
        points=False)

    reviews_box_plot.update_layout(
        template="plotly_dark",
        height=700,
        xaxis_tickangle=90,
        title = {
            "text": "<span style='font-size:25px'> Les jeux avec plus d'acheteurs reçoivent plus d'avis </span>"
        })

    reviews_box_plot.update_yaxes(type="log")

    st.plotly_chart(reviews_box_plot)
            ### /Reviews ###

            ### Release ###
    release_line = px.line(
        games_per_year,
        x="Release Year",
        y="Number of Games",)

    release_line.update_traces(
    mode="lines",
    line=dict(width=3, color="#3b5bdb"))

    release_line.update_layout(
        template="plotly_dark",
        height=500,

        title={
            "text": "<span style='font-size:20px;color:#ffffff;'>Les sorties de jeux sur Steam ont explosé à travers ces dernières décennies</span><br>"
                "<span style='font-size:15px;color:#ffffff;'>Nombre annuel de jeux sortis sur Steam</span>"},

        xaxis_title=None,
        yaxis_title="Games Released",

        xaxis_showgrid=False,
        yaxis=dict(
            showgrid=False,
            tickvals=[0, 5000, 10000, 15000],
            ticktext=["0", "5K", "10K", "15K"]))

    release_line.add_annotation(
        x=1,
        y=-0.18,
        xref="paper",
        yref="paper",
        text="Données disponibles jusqu'à 2024",
        showarrow=False,
        font=dict(size=12, color="#ffffff"),
        xanchor="right")

    # Add a marker only on the peak year (2024).
    release_line.add_scatter(
        x=[2024],
        y=[games_per_year.loc[games_per_year["Release Year"] == 2024, "Number of Games"].values[0]],
        mode="markers",
        marker=dict(
            size=10,
            color="#3b5bdb",
            line=dict(width=2, color="white")
        ),
        showlegend=False
    )

    release_line.add_annotation(
        x=2017.5,
        y=8000,
        text="Les sorties sur Steam ont multiplié par 10 entre 2014 et 2024",
        showarrow=True,
        font=dict(size=13, color="#ffffff")
    )

    # Only show meaning full data
    release_line.update_xaxes(range=[2004, 2024 + 0.07])

    st.plotly_chart(release_line)

    st.title("Notes")
    st.markdown("Le marché est en croissance constante et explosive. Lorsque l'offre est très largement supérieure à la demande, se démarquer est une réelle problématique.")
            ### /Release ###
    
with solutionPage:
    st.title("L'analyse du marché de Steam est claire : ")
    st.markdown(
    "- Le marché est saturé et en croissance explosive\n" 
    "- La distribution est ultra inégale\n" 
    "- La rétention des joueurs est plus forte sur les jeux payants\n" 
    "- Le succès est fortement corrélé à la visibilité\n" 
    )

    st.markdown("Plusieurs axes peuvent être explorés pour améliorer cette situation.")

    st.title("L'union fait la force")
    st.image(image="PieceByPiece.PNG",
             caption = "Le cas des deux jeux Piece by Piece. Les deux jeux portant un nom similaire sont sortis (quasiment) en même temps sur Steam. " \
             "Plutôt que d'en venir à des mesures juridiques, les deux studios ont décidé de créer un bundle contenant les deux jeux. ")
    st.markdown("Les jeux avec un prix abordable ont de meilleures chances d'être vendus donc les bundles sont une clé de voute pour booster les ventes.")

    st.title("Augmenter sa visibilité")
    st.image(image = "EarlyAccess.PNG",
             caption = "Beaucoup de jeux le font déjà mais la sortie en early access augmente le nombre de ventes à la sortie du jeu. Le bouche à oreille est" \
             "crucial.")
    st.markdown("Il ne faut pas sous-estimer l'impact des réseaux sociaux et le rôle des influenceurs pour la promotion d'un jeu. Et de tout faire pour apparaître dans" \
    " la wishlist (liste de souhaits) du plus grand nombre de joueurs. Steam met plus facilement en avant un projet ayant un grand nombre de wishlist.")
    
    st.title("Bien calculer son timing")
    st.image(image="Releases.PNG")
    st.markdown("Pour la sortie d'un jeu indé, il vaut mieux viser des périodes où peu de grosses licences (AAA) sortent en même temps. " \
    "Il faut également cibler une sortie lors d'une période de discount de Steam comme les soldes de printemps où les sorties sont faibles mais les achats sont importants.")

    st.text("Ceci est une humble étude Data du marché du jeu-vidéo sur Steam. Elle ne garantit pas à 100% le succès d'un projet mais vise à donner des recommandations" \
    "et aider les studios indés dans leur démarche de produire et promouvoir un jeu.")

    st.text("Cette étude a été réalisée grâce au dataset publié par Martin Bustos Roman sur Kaggle")
    st.link_button(label = "Dataset", url = "https://www.kaggle.com/datasets/fronkongames/steam-games-dataset/data")
    st.text("Et au dataset collecté par FronkonGames")
    st.link_button(label = "FronkonGames", url ="https://github.com/FronkonGames")
############################ /Charts ####################################