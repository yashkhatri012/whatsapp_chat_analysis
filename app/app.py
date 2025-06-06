import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns
import zipfile
import io
instructions_container = st.empty()  # Create an empty container for instructions

# Display instructions inside the container
with instructions_container:
    st.title("How To Use: ")
    st.markdown("""
        ### 📌 **Instructions:**
        0. click on the top left to open the side bar 
        1. Open the **WhatsApp** chat you want to analyze.
        2. Tap on the **three dots** (top-right corner) → **More** → **Export Chat**.
        3. Choose **Without Media** (this will generate a **.txt** file).
        4. Upload the exported **.txt** file or a **.zip** file containing chat exports to start the analysis.
        """)

st.sidebar.title("Whatsapp Chat Analyzer")

uploaded_file = st.sidebar.file_uploader("Choose a file", type=["txt", "zip"])
if uploaded_file is not None:
    # Process the file based on its extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'zip':
        # Handle zip file
        with zipfile.ZipFile(uploaded_file) as z:
            # Get list of text files in the zip
            txt_files = [f for f in z.namelist() if f.endswith('.txt')]
            
            if not txt_files:
                st.error("No text files found in the zip archive. Please upload a zip containing WhatsApp chat exports.")
            else:
                # If multiple files, let user select which one to analyze
                if len(txt_files) > 1:
                    selected_file = st.sidebar.selectbox("Select which chat to analyze:", txt_files)
                else:
                    selected_file = txt_files[0]
                 
                # Extract the selected file
                with z.open(selected_file) as file:
                    data = file.read().decode("utf-8")
                st.sidebar.success(f"Successfully extracted: {selected_file}")
    else:
        # Handle txt file directly
        bytes_data = uploaded_file.getvalue()
        data = bytes_data.decode("utf-8")
    
    # Process the data
    df = preprocessor.preprocess(data)

    # Check if preprocessing was successful
    if df.empty:
        st.error("No messages could be extracted from the file. Please check if it's a valid WhatsApp chat export.")
    else:
        # fetch unique users
        user_list = df['user'].unique().tolist()
        if 'group_notification' in user_list:
            user_list.remove('group_notification')
        user_list.sort()
        user_list.insert(0,"Overall")
        selected_user = st.sidebar.selectbox("Show analysis wrt",user_list)

        if st.sidebar.button("Show Analysis"): 
            instructions_container.empty()
            num_messages , num_media_messages , num_links =helper.fetch_stats(selected_user, df)
            st.title("Top Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.header("Total Messages")
                st.title(num_messages)
            with col2:
                st.header("Media Shared")
                st.title(num_media_messages)

            with col3:
                st.header("Links Shared")
                st.title(num_links)
            #Monthly timeline
            st.header("Monthly Timeline")
            timeline=helper.monthly_timeline(selected_user,df)

            fig , ax =plt.subplots()
            ax.plot(timeline['timeline'], timeline['message'])
            plt.xticks(rotation='vertical')
            st.pyplot(fig)
    
            #daily timeline
            st.title("Daily Timeline")
            daily_timeline = helper.daily_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)


            #Activity Map
            st.title("Activity Map")
            col1, col2 = st.columns(2)

            with col1:
                st.header("Most Active Day")
                busy_day= helper.week_activity_map(selected_user,df)
                fig , ax =plt.subplots()
                ax.bar(busy_day.index, busy_day.values)
                plt.xticks(rotation= 'vertical')
                st.pyplot(fig)
            with col2:
                st.header("Most Active Month")
                busy_month= helper.month_activity_map(selected_user,df)
                fig , ax =plt.subplots()
                ax.bar(busy_month.index, busy_month.values , color='#044291')
                plt.xticks(rotation= 'vertical')
                st.pyplot(fig)


            st.title("Weekly Activity Map")
            st.write("🔥 **Light Colors:**  Active | 🌑 **Dark Colors:** Inactive")
            user_heatmap=helper.activity_heatmap(selected_user,df)
            fig , ax =plt.subplots()
            ax=sns.heatmap(user_heatmap)

            st.pyplot(fig)



            if selected_user== 'Overall':
                st.title("Most Active Users")
                x, new_df = helper.active_users(df)
                fig , ax =plt.subplots()
                col5, col6 = st.columns(2)
                with col5:
                    ax.bar(x.index, x.values , color='#4682B4')
                    plt.xticks(rotation= 'vertical')
                    st.pyplot(fig)
                
                with col6:
                    
                    st.dataframe(new_df ,  width=1000 , column_config={
            new_df.columns[0]: st.column_config.Column(width="small"),  # Index/Name
            # Percent
        })
            st.title("WordCloud")
            df_wc= helper.word_cloud(selected_user,df)
            fig , ax =plt.subplots()
            ax.imshow(df_wc)
            st.pyplot(fig)
    
            
            # most common words
            most_common_df = helper.most_common_words(selected_user,df)

            fig,ax = plt.subplots()

            ax.barh(most_common_df[0],most_common_df[1])
            plt.xticks(rotation='vertical')

            st.title('Most commmon words')
            st.pyplot(fig)

    
            #emoji analysis
            emoji_df = helper.emoji_helper(selected_user,df)
            st.title("Emoji Analysis")


            col1, col2= st.columns(2)

            with col1:
                st.dataframe(emoji_df,width= 300)
            with col2:

                fig,ax = plt.subplots()
                ax.pie(emoji_df["count"].head(), labels=emoji_df["emoji"].head(), autopct="%0.2f")

                st.pyplot(fig)
