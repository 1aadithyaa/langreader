import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import session
import sqlite3
import random
import corpus
from dictionary import find_def
import pickle
import langreader.sort.prelim_sort as ps
import numpy as np
import datetime

# DB Management
conn1 = sqlite3.connect("resources/sqlite/corpus.sqlite")
c1 = conn1.cursor()

# session state
ss = session.get(user_info=None, index=None, button_submitted=False, checklist_submitted=False, done_setting_up=False, 
    corpus_length=None, order_strings=None, text_type=None,
    params=None)


def set_ss(indix):
    ss.index = indix #TODO: get rid of ss.index
    ss.params = corpus.get_all(ss.text_type, ss.order_strings[indix])


def set_text_type(text_type):
    if ss.text_type != text_type:
        ss.text_type = text_type
        ss.corpus_length = corpus.get_corpus_length(ss.text_type)
        ss.order_strings = corpus.get_order_strings(ss.text_type)
        ss.index = None
        ss.params = None


# initialization
def initialization():
    # if not ss.index:
    #     last_index = get_last(ss.text_type)
    #     if not last_index and last_index != 0:
    #         ss.corpus_length = corpus.get_corpus_length(ss.text_type)
    #         ss.order_strings = corpus.get_order_strings(ss.text_type)

    #         lower_bound = int(ss.corpus_length*.25)
    #         upper_bound = int(ss.corpus_length*.75)
    #         last_index = random.choice(range(lower_bound, upper_bound))

    #     set_ss(last_index)
    return


def main():
    global ss
    st.markdown(
            f"""
    <style>
        .reportview-container .main .block-container{{
            max-width: 70%;
        }}
    </style>
    
    """,
            unsafe_allow_html=True,
        )
    
    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True) # turn streamlit radio buttons horizontal
    st.markdown(
        """ <style>
                div[role="radiogroup"] >  :first-child{
                    display: none !important;
                }
            </style>
            """,
        unsafe_allow_html=True
    ) # don't display the first radio button  

    st.title("Project READ")

    if not ss.user_info:
        menu = ["Home", "Login", "Signup"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Home":
            st.subheader("Home")
        
        elif choice == "Login":
            login()
        
        elif choice == "Signup":
            signup()
        
        st.info("You are currently not logged in. Head to the Login tab on the sidebar menu.")
        
        welcome_text = """Welcome! Project READ is an up-and-coming application that enables English learners to enhance their reading comprehension in a fun, relevant context. Our platform provides short written pieces tailored to a user's interests and is designed to be used in <10 minutes each day."""
        
        st.write(welcome_text + "\n")
        st.write("**Diverse Corpus:** Users have access to a wide range of texts from short stories to news articles to poems.\n")
        st.write("**ML-driven:** While users have the ability to choose texts to read independently, Project READ constantly recommends texts based on a user's current reading level.\n")
        st.write("**Reading Aids:** Our application integrates a variety of reading tools, such as an in-platform dictionary and audio reader, to maximize the learning experience.\n")
        
        
    else:
        menu = ["Home", "Sign Out"]
        choice = st.sidebar.selectbox("Menu", menu)
        if choice == "Home":
            pass
        elif choice == "Sign Out":
            if st.sidebar.button("Log out"):
                reset()
        initialization()

        # print('user info:', ss.user_info)
        # print('params:', ss.params)
        if ss.user_info[7] or ss.user_info[6] is None: # 7 > first_time; 6 > user_profile
            first_time()
        else:
            run_application()


def record_level(language_level):
    level_int = -1
    if language_level == "A1":
        level_int = 1
    if language_level == "A2":
        level_int = 2
    if language_level == "B1":
        level_int = 3
    if language_level == "B2":
        level_int = 4
    if language_level == "C1":
        level_int = 5
    if language_level == "C2":
        level_int = 6
    if level_int == -1:
        return
    c1.execute('UPDATE UsersTable SET first_time = 0, recorded_level = ? WHERE user_id = ?', (level_int, ss.user_info[0]))
    conn1.commit()
    ss.user_info[7] = 0 # 7 > first_time
    ss.user_info[8] = level_int # 8 > level_int


def insert_user_profile(user_profile):
    up = pickle.dumps(user_profile)
    c1.execute('UPDATE UsersTable SET user_profile = ? WHERE user_id = ?', (up, ss.user_info[0])) # 0 > user_id
    conn1.commit()
    ss.user_info[6] = up # 6 > user_profile


def get_user_profile():
    return pickle.loads(ss.user_info[6]) # 6 > user_profile


def add_userdata(username, password): # returns whether sign up was successful
    c1.execute('SELECT * FROM UsersTable WHERE username = ?', (username,))
    if c1.fetchall():
        return False
    c1.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn1.commit()
    return True


def login_user(username, password):
    c1.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, password))
    data = c1.fetchall()[0]
    return list(data)


def view_all_users():
    c1.execute('SELECT * FROM userstable')
    data = c1.fetchall()
    return data


def get_column_name(text_type):
    column_name = None
    if text_type == "poem":
        column_name = "last_poem_id"
    elif text_type == "short_story":
        column_name = 'last_short_story_id'
    elif text_type == "news":
        column_name = 'last_news_id'
    return column_name


def get_last(text_type):
    c1.execute('SELECT ' + get_column_name(text_type) + ' FROM UsersTable WHERE username = ?', (ss.user_info[1],)) # 1 > username
    return c1.fetchone()[0]


def set_last(text_type):
    c1.execute('UPDATE UsersTable SET ' + get_column_name(text_type) + ' = ' + str(ss.index) + ' WHERE username = ?', (ss.user_info[1],)) # 1 > username
    conn1.commit()

    
def reset():
    ss.user_info = None 
    ss.index = None
    ss.button_submitted = False
    ss.checklist_submitted = False
    ss.done_setting_up = False
    ss.corpus_length = None
    ss.order_strings = None
    ss.text_type = None
    ss.params = None
    st.experimental_rerun()


def signup():
    st.sidebar.subheader("Create New Account")
    new_user = st.sidebar.text_input("Username")
    new_pass = st.sidebar.text_input("Password", type = "password")

    if st.sidebar.button("Signup"):
        if add_userdata(new_user, new_pass):
            st.sidebar.success("Successfully created a valid account")
            ss.user_info = login_user(new_user, new_pass)
            st.experimental_rerun()
        else:
            st.sidebar.error("Username already taken")


def login():
    st.sidebar.subheader("Login")

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type = "password")
    if st.sidebar.button("Login"):
        result = login_user(username, password)
        print("Result from login query: ", result)
        if result:
            ss.user_info = result
            st.experimental_rerun()
            #st.sidebar.success("Welcome, {}. Head back to the Home page.".format(ss.user_info[1])) # 1 > username
        else:
            st.sidebar.error("Error: Username/Password is incorrect")

# --record readability/enjoyability of text--
def record_difficulty_and_interest(difficulty, interest, user_id, article_id):
    difficulty_int = 1 if difficulty == 'Too Easy' else 2 if difficulty == 'Just Right' else 3 if difficulty == 'Too Hard' else -1
    interest_int = 1 if interest == 'Very Boring' else 2 if interest == 'Somewhat Interesting' else 3 if interest == 'Very Interesting' else -1
    
    status = 1
    date_time_completed = str(datetime.datetime.now())
    c1.execute('INSERT OR REPLACE INTO UserRatings VALUES (null, ?, ?, ?, ?, ?, ?)', (user_id, article_id, difficulty_int, interest_int, status, date_time_completed))
    conn1.commit()


# --helper methods--
def difference_bw_lists(old, new):
    diff = {}
    for o, n, index in zip(old, new, range(len(old))):
        if o != n:
            diff[index] = (o, n)
    return diff


def get_next_indices(difficulty, index):
    index_list = None
    if difficulty == 'Too Easy':
        interval = ss.corpus_length//19
    elif difficulty == 'Just Right':
        interval = 2
    elif difficulty == 'Too Hard':
        interval = ss.corpus_length//-31
    index_list = set(range(index + interval, index + interval*4, interval))

    # this won't work as new texts are added
    difference_set = set()
    for i in index_list:
        if i < 0 or i > ss.corpus_length - 1:
            difference_set.add(i)

    index_list -= difference_set

    if len(index_list) == 0:
        if index < ss.corpus_length/2:
            index_list = {0}
        else:
            index_list = {ss.corpus_length - 1}

    return index_list


def display_checklist(words_to_test):
    with st.form('checklist'):
        st.write('**Do you know these words?**\n(If you\'re not sure, you can leave it blank or select Not Sure.)')
        results = [None] * len(words_to_test)
        for word, windex in zip(words_to_test, range(len(words_to_test))):
            word_col, yes_no_col = st.beta_columns(2)
            with word_col:
                st.write(word)
            with yes_no_col:
                result = st.radio('', ['-', 'Yes', 'No', 'Not Sure'], key=windex)
                if result == 'Yes':
                    results[windex] = 1
                elif result == 'No':
                    results[windex] = -1
                else:
                    results[windex] = 0
                
        if st.form_submit_button():
            return results
        else:
            return None


def first_time(): #TODO: insert plausible-sounding fake words to ensure that data is correct
    st.write("Hello, {}! For us to recommend you texts that accurately match your readability, we need to know a little bit more about your English language skills.".format(ss.user_info[1])) # 1 > username
    st.write("What language level are you?")
    language_level = st.radio("CEFR Language Levels", ["-", "A1", "A2", "B1", "B2", "C1", "C2"])
    if language_level != "-":
        word_vector = ps.get_baseline_profile_from_level(language_level)
        random_words = ps.get_weighted_random_words_from_profile(word_vector, 1000, 50)
        new_values = display_checklist(random_words)
        print("new_values:", new_values is not None)
        if new_values:
            ps.update_profile(word_vector, random_words, new_values)
            record_level(language_level)
            insert_user_profile(word_vector)
            st.experimental_rerun()

            
#TODO: add functionality for adding a new text to corpus if the user wants to
def run_application():
    print("running 3; Printing because index is {}".format(ss.index))
    # set_last(ss.text_type) #TODO: delete set_last
    if ss.params: # i.e. if params exists
        text_selected()
    else:
        home_logged_in()


def home_logged_in():
    st.success("Welcome, {}!".format(ss.user_info[1])) # 1 > username
    # TODO: implement unfinished_texts
    # unfinished_texts = get_unfinished_texts()
    # if unfinished_texts:
    #     st.write("**Pick Up Where You Left Off**")
    display_recommendations(5)


def display_recommendations(n):
    st.write("**Recommendations**")
    st.write("Poems")
    get_recommendations("poem", n)
    st.write("Short Stories")
    get_recommendations("short_story", n)
    st.write("News")
    get_recommendations("news", n)



def get_recommendations(text_type, n):
    up = get_user_profile()
    recommendations = ps.get_top_k_texts_from_user_profile(up, text_type, n, ss.user_info[0]) # 0 > user_id
    for text, column in zip(recommendations, st.beta_columns(len(recommendations))):
        with column:
            if st.button(text[1]): # 1 > the recommended text's title
                ss.params = corpus.get_all_from_id(text[0]) # 0 > the recommended text's id
                st.experimental_rerun()


def get_weighted_random_hard_words_from_text(fv, n):
    words = []
    p_dist = []

    for key in fv.keys():
        log_rank = ps.rank_dictionary.get(key)
        if not log_rank:
            continue
        words.append(key)
        p_dist.append(log_rank)
    
    n = min(len(words), n)
    
    print(words)

    total = sum(p_dist)
    p_dist = [j/total for j in p_dist]
    
    return [i for i in np.random.choice([j for j in words], n, p=p_dist, replace=False)]
        

def update_and_record_profile(words, new_values):
    up = pickle.loads(ss.user_info[6]) # 6 > user_profile
    ps.update_profile(up, words, new_values)
    insert_user_profile(up)


def text_selected():
    # st.write(ss.index + 1, '/', ss.corpus_length)
    # st.progress(ss.index / ss.corpus_length)
    if not ss.checklist_submitted:
        #TODO: implement text status check
        # if this is the first time the user has seen the text:

        hard_words = get_weighted_random_hard_words_from_text(pickle.loads(ss.params[11]), 10) # 11 > frequency_vector
        new_values = display_checklist(hard_words) # 11 > frequency_vector
        print('hard words:', hard_words)
        print('new values:', new_values)
        if new_values:
            update_and_record_profile(hard_words, new_values)
            ss.checklist_submitted = True
            st.experimental_rerun()

    st.markdown("**Please read the text carefully.**")
    st.markdown("**_" + ss.params[1].strip() + "_**") # 1 > article_title
    print('author:', ss.params[9]) # 9 > article_author
    print('text:', True if ss.params[2] else False) # 2 > article_text
    print('url:', ss.params[3]) # 3 > article_url
    if ss.params[9]: # 9 > article_author
        st.markdown("*by " + ss.params[9] + "*")
    if not ss.params[2]: # 2 > article_text
        print("Param 3: ", ss.params[3])
        st.write(f'<iframe src="' + ss.params[3] + '" height="900" width="800"></iframe>', unsafe_allow_html=True)
    else:
        if ss.params[3]: # 3 > article_url
            st.write(ss.params[3])
        # if '\n' in ss.params[2].strip():
        #     st.code(ss.params[2], language="")
        # else:
        #     st.write(ss.params[2])

        # dictionary feature
        col_text, col_controls = st.beta_columns((3,2))
        with col_text:
            st.write(ss.params[2])
        with col_controls:
            dictionary_expander = st.beta_expander(label = "Dictionary", expanded = True)
            with dictionary_expander:
                word = st.text_input("Get the definition of an unfamiliar word")
                if word:
                    try:
                        word_text = find_def(word)
                        if not word_text:
                            word_text = """Error: Unable to get word's definition"""
                        else:
                            update_and_record_profile(v.preprocess(word), [-1])
                    except Exception:
                        word_text = """Error: Unable to get word's definition"""
                    st.markdown(word_text)

    with st.form('difficulty_selector'):
        difficulty = st.select_slider(
            'How hard is this text for you?',
            options=['Too Easy', 'Just Right', 'Too Hard'])
        interest = st.select_slider(
            'How interesting is this text for you?',
            options=['Very Boring', 'Somewhat Interesting', 'Very Interesting']
        )
        submit = st.form_submit_button('Get Another Text!')
    
    print('button_submitted:', ss.button_submitted, "sumbit:", submit)
    if ss.button_submitted or submit: #TODO: make sure user doesn't get the same text twice!
        print("running 4; button pressed")

        record_difficulty_and_interest(difficulty, interest, ss.user_info[0], ss.params[0]) # 0 > user_id; 0 > article_id

        ss.button_submitted = True
        
        display_recommendations(3)

        # st.write('Here are some texts we thought would be appropriate:')

        # next_indices = get_next_indices(difficulty, ss.index)

        # ss.button_submitted = True # the button resets to False even if one of its children are pressed, so a persistent state is needed

        # for column, indix in zip(st.beta_columns(len(next_indices)), next_indices):
        #     title = corpus.get_all(ss.text_type, ss.order_strings[indix])[1] # 1 > title

        #     with column:
        #         if st.button(title): 
        #             print('running 5; button pressed')
        #             set_ss(indix)
        #             ss.button_submitted = False
        #             st.experimental_rerun()
        

        # # with st.form('explicit_number'):
        # #     explicit_index = st.number_input('Or, go enter an index from 0 to ' + str(ss.corpus_length - 1) + ' to go to a custom text.', min_value=0, max_value=ss.corpus_length-1)
        # #     num_submit = st.form_submit_button()
        # # if num_submit:
        # #     print('running 5; button pressed')
        # #     set_ss(explicit_index)
        # #     ss.button_submitted = False
        # #     st.experimental_rerun()      


if __name__ == '__main__':
    main()

