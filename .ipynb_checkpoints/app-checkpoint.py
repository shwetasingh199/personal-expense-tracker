import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

from auth import (
    create_user_table,
    create_user,
    login_user
)

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="Personal Expense Tracker",
    layout="wide"
)

# =====================================
# DATABASE CONNECTION
# =====================================

def connect_db():
    return sqlite3.connect("expense_tracker.db")


# =====================================
# CREATE TABLES
# =====================================

def create_tables():

    conn = connect_db()
    cursor = conn.cursor()

    # Categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # Transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category_id INTEGER,
        amount REAL CHECK(amount > 0),
        payment_method TEXT,
        note TEXT
    )
    """)

    categories = [
        "Food",
        "Transport",
        "Shopping",
        "Bills",
        "Entertainment",
        "Health",
        "Education",
        "Other"
    ]

    for cat in categories:

        cursor.execute("""
        INSERT OR IGNORE INTO categories(name)
        VALUES(?)
        """, (cat,))

    conn.commit()
    conn.close()


# =====================================
# ADD EXPENSE
# =====================================

def add_expense(date, category, amount, payment, note):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM categories
    WHERE name=?
    """, (category,))

    category_id = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO transactions
    (date, category_id, amount, payment_method, note)
    VALUES (?, ?, ?, ?, ?)
    """, (
        str(date),
        category_id,
        amount,
        payment,
        note
    ))

    conn.commit()
    conn.close()


# =====================================
# FETCH DATA
# =====================================

def fetch_data():

    conn = connect_db()

    query = """
    SELECT
        t.id,
        t.date,
        c.name AS category,
        t.amount,
        t.payment_method,
        t.note
    FROM transactions t
    JOIN categories c
    ON t.category_id = c.id
    ORDER BY t.date DESC
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    if not df.empty:

        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.strftime("%Y-%m")

    return df


# =====================================
# KPI
# =====================================

def calculate_kpis(df):

    if df.empty:
        return 0, 0, "N/A"

    total = df["amount"].sum()

    avg_daily = (
        df.groupby("date")["amount"]
        .sum()
        .mean()
    )

    top_category = (
        df.groupby("category")["amount"]
        .sum()
        .idxmax()
    )

    return total, avg_daily, top_category


# =====================================
# FORMAT
# =====================================

def format_currency(amount):
    return f"₹{amount:,.0f}"


# =====================================
# INITIALIZE
# =====================================

create_tables()
create_user_table()

# =====================================
# SESSION STATE
# =====================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =====================================
# LOGIN / SIGNUP PAGE
# =====================================

if not st.session_state.logged_in:

    st.title("🔐 Personal Expense Tracker")

    menu = st.sidebar.selectbox(
        "Menu",
        ["Login", "Create Account"]
    )

    # LOGIN
    if menu == "Login":

        st.subheader("Login")

        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login"):

            result = login_user(username, password)

            if result:

                st.session_state.logged_in = True
                st.success("✅ Login Successful")
                st.rerun()

            else:

                st.error("❌ Invalid Credentials")

    # SIGNUP
    else:

        st.subheader("Create Account")

        new_user = st.text_input("Username")
        new_pass = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Create Account"):

            success = create_user(new_user, new_pass)

            if success:

                st.success("✅ Account Created Successfully")

            else:

                st.error("⚠️ Username Already Exists")


# =====================================
# MAIN DASHBOARD
# =====================================

else:

    df = fetch_data()

    st.title("💳 Personal Expense Tracker")

    # LOGOUT
    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.rerun()

    # =====================================
    # ADD EXPENSE
    # =====================================

    st.subheader("➕ Add Expense")

    conn = connect_db()

    categories = pd.read_sql(
        "SELECT name FROM categories",
        conn
    )["name"].tolist()

    conn.close()

    col1, col2, col3, col4, col5 = st.columns(5)

    expense_date = col1.date_input(
        "Date",
        datetime.today()
    )

    category = col2.selectbox(
        "Category",
        categories
    )

    amount = col3.number_input(
        "Amount (₹)",
        min_value=1.0,
        step=50.0
    )

    payment = col4.selectbox(
        "Payment",
        ["UPI", "Cash", "Card"]
    )

    note = col5.text_input("Note")

    if st.button("Add Expense"):

        if note.strip() == "":

            st.warning("⚠️ Add description")

        else:

            add_expense(
                expense_date,
                category,
                amount,
                payment,
                note
            )

            st.success("✅ Expense Added")
            st.rerun()

    st.divider()

    # =====================================
    # INSIGHTS
    # =====================================

    if df.empty:

        st.info("No expenses added yet")

    else:

        months = sorted(
            df["month"].unique(),
            reverse=True
        )

        selected_month = st.selectbox(
            "Select Month",
            months
        )

        filtered_df = df[
            df["month"] == selected_month
        ]

        total, avg_daily, top_category = calculate_kpis(filtered_df)

        budget = st.number_input(
            "Set Monthly Budget",
            value=10000
        )

        remaining = budget - total

        k1, k2, k3, k4 = st.columns(4)

        k1.metric(
            "💰 Total",
            format_currency(total)
        )

        k2.metric(
            "📅 Avg Daily",
            format_currency(avg_daily)
        )

        k3.metric(
            "🏆 Top Category",
            top_category
        )

        if remaining >= 0:

            k4.metric(
                "💸 Remaining",
                format_currency(remaining)
            )

        else:

            k4.metric(
                "🚨 Over Budget",
                format_currency(abs(remaining))
            )

        # =====================================
        # CHARTS
        # =====================================

        c1, c2 = st.columns(2)

        trend = (
            filtered_df
            .groupby("date")["amount"]
            .sum()
            .reset_index()
        )

        if trend.shape[0] > 1:

            fig1 = px.line(
                trend,
                x="date",
                y="amount",
                markers=True,
                title="📈 Spending Trend"
            )

            c1.plotly_chart(
                fig1,
                use_container_width=True
            )

        else:

            c1.info(
                "Add expenses on multiple dates"
            )

        cat = (
            filtered_df
            .groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        fig2 = px.pie(
            cat,
            names="category",
            values="amount",
            hole=0.5,
            title="📊 Category Distribution"
        )

        c2.plotly_chart(
            fig2,
            use_container_width=True
        )

        # =====================================
        # TABLE
        # =====================================

        st.subheader("📋 Transactions")

        st.dataframe(
            filtered_df,
            use_container_width=True
        )