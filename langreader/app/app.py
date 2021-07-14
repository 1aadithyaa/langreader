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

# DB Management
conn1 = sqlite3.connect("resources/sqlite/corpus.sqlite")
c1 = conn1.cursor()

# session state
ss = session.get(user_info=None, index=None, button_submitted=False, done_setting_up=False, 
    corpus_length=None, order_strings=None, text_type=None,
    params=None) # TODO: add a language variable


def set_ss(indix):
    ss.index = indix
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
    if not ss.index:
        last_index = get_last(ss.text_type)
        if not last_index and last_index != 0:
            ss.corpus_length = corpus.get_corpus_length(ss.text_type)
            ss.order_strings = corpus.get_order_strings(ss.text_type)

            lower_bound = int(ss.corpus_length*.25)
            upper_bound = int(ss.corpus_length*.75)
            last_index = random.choice(range(lower_bound, upper_bound))

        set_ss(last_index)


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
        menu = ["Poems", "Short Stories", "Sign Out"]
        choice = st.sidebar.selectbox("Menu", menu)
        if choice == "Poems":
            set_text_type('poem')
        elif choice == "Short Stories":
            set_text_type("short_story")
        elif choice == "News":
            set_text_type("news")
        elif choice == "Sign Out":
            if st.sidebar.button("Log out"):
                reset()
        initialization()

        if ss.user_info[7]: # 7 > first_time
            st.write("Hello, {}! For us to recommend you texts that accurately match your readability, we need to know a little bit more about your English language skills.".format(ss.user_info[1])) # 1 > username
            st.write("What language level are you?")
            language_level = st.radio("CEFR Language Levels", ["-", "A1", "A2", "B1", "B2", "C1", "C2"])
            if language_level != "-":
                word_vector = ps.get_baseline_profile_from_level(language_level)
                print(display_checklist(ps.get_weighted_random_words_from_profile(word_vector, 1000, 50)))
        else:
            run_application()

def insert_user_profile(user_profile):
    up = pickle.dumps(user_profile)
    c1.execute('UPDATE UsersTable SET user_profile = ? WHERE user_id = ?', (up, ss.user_info[0])) # 0 > user_id
    conn1.commit()


def get_user_profile():
    c1.execute('SELECT user_profile FROM UsersTable WHERE user_id = ?', (ss.user_info[0],))
    return pickle.loads(c1.fetchone()[0])


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
    return data


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
def record_difficulty_and_interest(difficulty, interest, username, language, text_type, order_string):
    c1.execute('SELECT user_id FROM UsersTable WHERE username = ?', (username, ))
    user_id = c1.fetchone()[0]
    c1.execute('SELECT article_id FROM Repository WHERE language = ? AND text_type = ? AND order_string = ?', (language, text_type, order_string))
    article_id = c1.fetchone()[0]

    difficulty_int = 1 if difficulty == 'Too Easy' else 2 if difficulty == 'Just Right' else 3 if difficulty == 'Too Hard' else -1
    interest_int = 1 if interest == 'Very Boring' else 2 if interest == 'Somewhat Interesting' else 3 if interest == 'Very Interesting' else -1
    
    c1.execute('INSERT OR REPLACE INTO UserRatings VALUES (null, ?, ?, ?, ?)', (user_id, article_id, difficulty_int, interest_int))
    conn1.commit()


# --helper methods--
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
        st.write('**Do you know these words?**')
        results = [None] * len(words_to_test)
        for word, windex in zip(words_to_test, range(len(words_to_test))):
            word_col, yes_no_col = st.beta_columns(2)
            with word_col:
                st.write(word)
            with yes_no_col:
                result = st.radio('', ['-', 'Yes', 'No', 'Not sure'], key=windex)
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


#TODO: add functionality for adding a new text to corpus if the user wants to
def run_application():
    print("running 3; Printing because index is {}".format(ss.index))
    set_last(ss.text_type)
    st.success("Welcome, {}!".format(ss.user_info[1])) # 1 > username

    print("hello, everybody:", display_checklist(['ape'] * 50))
    
    st.write(ss.index + 1, '/', ss.corpus_length)
    st.progress(ss.index / ss.corpus_length)
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
                    except Exception:
                        word_text = """Error: Unable to get word's definition"""
                    st.markdown(word_text)

    with st.form('hi'):
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

        record_difficulty_and_interest(difficulty, interest, ss.user_info[1], 'english', ss.text_type,  ss.order_strings[ss.index]) # 1 > username

        st.write('Here are some texts we thought would be appropriate:')

        next_indices = get_next_indices(difficulty, ss.index)

        ss.button_submitted = True # the button resets to False even if one of its children are pressed, so a persistent state is needed

        for column, indix in zip(st.beta_columns(len(next_indices)), next_indices):
            title = corpus.get_all(ss.text_type, ss.order_strings[indix])[1] # 1 > title

            with column:
                if st.button(title): 
                    print('running 5; button pressed')
                    set_ss(indix)
                    ss.button_submitted = False
                    st.experimental_rerun()
        

        with st.form('explicit_number'):
            explicit_index = st.number_input('Or, go enter an index from 0 to ' + str(ss.corpus_length - 1) + ' to go to a custom text.', min_value=0, max_value=ss.corpus_length-1)
            num_submit = st.form_submit_button()
        if num_submit:
            print('running 5; button pressed')
            set_ss(explicit_index)
            ss.button_submitted = False
            st.experimental_rerun()      


if __name__ == '__main__':
    main()

