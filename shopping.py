import streamlit as st
import pandas as pd
import openai
import matplotlib.pyplot as plt
import os
import csv
import time

# Crear un DataFrame con productos

def pagina_principal():
    # Título de la aplicación
    st.title("Carrito de Compras")


    # Crear una función para cargar los datos de productos y cachearlos
    @st.cache_data
    def cargar_datos_productos():
        productos =  pd.read_csv(r'Productos.csv')
        return pd.DataFrame(productos)

    @st.cache_data
    def cargar_datos_apriori():
        apriori =  pd.read_csv(r'Apriori_top200.csv')
        return pd.DataFrame(apriori)
    
    # Inicializa el tiempo de inicio de la sesión cuando el usuario carga la página
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()

    # Cargar los datos de productos
    df_productos = cargar_datos_productos()
    df_apriori = cargar_datos_apriori()
    df_productos = df_productos.loc[df_productos.PRODUCT_NAME.isin(df_apriori.Left_Hand_Side.unique())]

    # Seleccionar productos para agregar al carrito
    st.subheader("Agregar al Carrito:")
    producto_seleccionado = st.selectbox("Selecciona un producto:", df_productos['PRODUCT_NAME'])
    cantidad_seleccionada = st.number_input("Cantidad:", min_value=1)

    # Crear una función para cargar y cachear el carrito de compras
    @st.cache_resource
    def cargar_carrito():
        return {}

    # Cargar y actualizar el carrito de compras
    carrito = cargar_carrito()
    
    # Calcula el tiempo transcurrido desde el inicio de la sesión
    current_time = time.time()
    elapsed_time = current_time - st.session_state.start_time
    print(elapsed_time)
    
    seconds = int(elapsed_time % 60)
    
    if (elapsed_time >10) and (20 > elapsed_time):
        st.toast('Hoy tu combo favorito de Café con Galletas está en promoción 😋')
        
    elif (elapsed_time >20) and (30 > elapsed_time):
        st.toast('En 7 Eleven tenemos tu café listo para comenzar ☕')

    elif (elapsed_time >30) and (40 > elapsed_time):
        st.toast('¿A todo gas? A 600 metros tenemos una Petro Seven ⛽')
        
    if st.button("Agregar al Carrito"):
        texto_success = 'El producto ' + producto_seleccionado + ' fue agregado con éxito a tu carrito.'
        st.toast(texto_success)
        st.balloons()
        st.subheader('Hey, quizás te interesen estos productos')
        filtro = df_apriori.loc[df_apriori.Left_Hand_Side == producto_seleccionado].sort_values(by = 'Confidence', ascending = False)
        options = df_productos.loc[df_productos.PRODUCT_NAME.isin(filtro['Right_Hand_Side'].values)][['PRODUCT_NAME', 'UNIT_PRICE']]
        
        for i,j in options.values:
            texto = i + ' está a ' + str(j) + ' MXN'
            st.success(texto)
        
        if producto_seleccionado in carrito:
            carrito[producto_seleccionado] += cantidad_seleccionada
        else:
            carrito[producto_seleccionado] = cantidad_seleccionada
            
    # Mostrar el contenido del carrito
    st.subheader("Carrito de Compras:")
    if not carrito:
        st.write("El carrito está vacío.")
    else:
        for producto, cantidad in carrito.items():
            st.write(f"{producto}: {cantidad} unidades")

    # Calcular el total del carrito
    total = sum(df_productos.loc[df_productos['PRODUCT_NAME'] == producto]['UNIT_PRICE'].values[0] * cantidad for producto, cantidad in carrito.items())
    st.subheader(f"Total del Carrito: ${total:.2f}")
    
def chatbot():
        

    # Inicializa la clave API de OpenAI (Recomendado: Usa una variable de entorno para más seguridad)
    openai.api_key = "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"

    # Función para hacer preguntas al modelo
    def ask_gpt3(question):
        model_engine = "davinci:ft-personal-2023-09-23-04-38-52"  # O el modelo que prefieras
        response = openai.Completion.create(
            engine=model_engine,
            prompt=question,
            max_tokens=100
        )
        message = response['choices'][0]['text'].strip()
        
        # Corta la respuesta si encuentra el símbolo "¿"
        cut_index = message.find("¿")
        if cut_index != -1:
            message = message[:cut_index]
        
        return message

    # Función para guardar la consulta del usuario en un archivo txt
    def save_to_txt(user_input):
        with open("consultas.txt", "a") as f:
            f.write(f"{user_input}\n")

    # Función para analizar el sentimiento de una consulta
    def analyze_sentiment(query):
        prompt = f"Decide si el sentimiento de un Tweet es positivo, neutral, o negativo.\n\nTweet: \"{query}\"\nSentiment:"
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=60,
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.0
        )
        
        sentiment = response.choices[0].text.strip().lower()
        
        # Validación adicional para asegurarse de que el sentimiento está en las categorías esperadas
        if sentiment not in ["positivo", "neutral", "negativo"]:
            sentiment = "Indeterminado"
        
        return sentiment

    # Función para guardar el sentimiento en un archivo CSV
    def save_to_csv(query, sentiment):
        with open('sentiments.csv', mode='a') as file:
            writer = csv.writer(file)
            writer.writerow([query, sentiment])

    # Interfaz de Streamlit
    st.title("Chatbot de Atención al Cliente 24/7")

    # Menú de selección para las pestañas
    option = st.sidebar.selectbox(
        'Selecciona una opción',
        ('Chatbot', 'Análisis de Sentimientos')
    )

    if option == 'Chatbot':
        # Ingresa una nueva pregunta
        user_input = st.text_input("Hazme una pregunta:")

        # Botón para enviar la pregunta
        if st.button("Enviar"):
            # Guarda la consulta del usuario en un archivo txt
            save_to_txt(user_input)
            # Haz la pregunta al modelo
            st.write("Pensando...")
            response = ask_gpt3(user_input)
            st.write("Respuesta:", response)

    elif option == 'Análisis de Sentimientos':
        # Botón para analizar el sentimiento de las consultas en consultas.txt
        if st.button("Analizar Sentimiento de Consultas"):
            if os.path.exists("consultas.txt"):
                sentiment_counts = {"positivo": 0, "neutral": 0, "negativo": 0, "indeterminado": 0}
                total = 0
                with open("consultas.txt", "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        sentiment = analyze_sentiment(line.strip())
                        if sentiment in sentiment_counts:
                            sentiment_counts[sentiment] += 1
                        total += 1
                        save_to_csv(line.strip(), sentiment)
                
                # Calcula los porcentajes
                sentiment_percentages = {k: (v / total) * 100 for k, v in sentiment_counts.items()}
                
                # Crea la gráfica de barras
                plt.figure(figsize=(10, 6))
                plt.bar(sentiment_percentages.keys(), sentiment_percentages.values(), color=['green', 'blue', 'red', 'gray'])
                plt.xlabel('Sentimiento')
                plt.ylabel('Porcentaje (%)')
                plt.title('Distribución de Sentimientos')
                for i, (k, v) in enumerate(sentiment_percentages.items()):
                    plt.text(i, v, f"{v:.2f}%", ha='center')
                
                # Muestra la gráfica en Streamlit
                st.pyplot(plt)
                
                st.write("Análisis de sentimiento completado y guardado en sentiments.csv.")
            else:
                st.write("El archivo consultas.txt no existe.")
            

st.set_page_config(page_title='Iconn Hacks', page_icon = '7ELEVENICON.png', initial_sidebar_state = 'auto')    
images = ['seven.png', 'iconn.jpg']
left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image(images, width = 100, caption=[""] * len(images))
pagina = st.selectbox("Selecciona una página", ["Carrito de compras", "Chat-bot"])

# Mostrar la página seleccionada
if pagina == "Carrito de compras":
    pagina_principal()
elif pagina == "Chat-bot":
    chatbot()




