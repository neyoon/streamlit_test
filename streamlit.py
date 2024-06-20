import streamlit as st
import sqlite3

# 创建SQLite连接
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def get_random_pair():
    """从数据库中随机获取一个对话对ID"""
    cursor.execute("SELECT DISTINCT pair FROM conversations WHERE user_id = 'test_user' ORDER BY RANDOM() LIMIT 1")
    return cursor.fetchone()

def get_conversations_by_pair(pair):
    """根据对话对ID获取对话详细信息"""
    cursor.execute("SELECT id, human_question, ai_answer, choice FROM conversations WHERE pair = ? AND user_id = 'test_user'", (pair,))
    return cursor.fetchall()

def update_choice(pair, selected_id, user_id):
    """更新对话的选择状态，并记录用户完成的对话数"""
    cursor.execute("UPDATE conversations SET choice = CASE WHEN id = ? THEN 1 ELSE 0 END, user_id = ? WHERE pair = ? AND user_id = ?", (selected_id, user_id, pair, user_id))
    conn.commit()
    cursor.execute("INSERT INTO user_progress (user_id, completed_pairs) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET completed_pairs = completed_pairs + 1", (user_id,))
    conn.commit()
    cursor.execute("UPDATE conversations SET user_id = ? WHERE pair = ?", (user_id, pair))
    conn.commit()
    
def check_completion(user_id):
    """检查用户是否已完成十五组对话"""
    cursor.execute("SELECT completed_pairs FROM user_progress WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result and result[0] >= 15:
        return True
    return False

def end_session():
    st.write("会话已结束。")
    st.stop()

if 'username' not in st.session_state:
    username = st.text_input("输入你的名字以继续:")
    if username:
        st.session_state['username'] = username
        st.session_state['pair'] = get_random_pair()

if 'pair' in st.session_state and st.session_state.username:
    pair = st.session_state['pair']
    if pair:
        pair_id = pair[0]
        conversations = get_conversations_by_pair(pair_id)
        if len(conversations) == 2:
            conversation1, conversation2 = conversations

            col1, col2 = st.columns(2)

            with col1:
                st.header("对话 1")
                st.subheader("选择时请双击")
                st.write(f"ID: {conversation1[0]}")
                st.chat_message("user").write(conversation1[1])
                st.chat_message("assistant").write(conversation1[2])
                if st.button(f"选择对话 1 (pair {pair_id})",key = f"{pair_id}1"):
                    update_choice(pair_id, conversation1[0], st.session_state['username'])
                    st.session_state['pair'] = get_random_pair() if not check_completion(st.session_state['username']) else None

            with col2:
                st.header("对话 2") 
                st.subheader("选择时请双击")
                st.write(f"ID: {conversation2[0]}")
                st.chat_message("user").write(conversation2[1])
                st.chat_message("assistant").write(conversation2[2])
                if st.button(f"选择对话 2 (pair {pair_id})",key = f"{pair_id}2"):
                    update_choice(pair_id, conversation2[0], st.session_state['username'])
                    st.session_state['pair'] = get_random_pair() if not check_completion(st.session_state['username']) else None

            if check_completion(st.session_state['username']):
                st.success("您已完成所有选择，感谢您的付出。")
                st.button("结束选择并记录", on_click=end_session)
        else:
            st.write("该pair内对话数量不足。",f"{pair_id}")
    else:
        st.write("没有找到对话对。")
        if st.button("Load New Pair"):
            st.session_state['pair'] = get_random_pair()