import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
st.set_page_config(
    page_title="金融431专属记录",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("""
    <style>
    header {visibility: hidden;}
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ====================== 登录验证 ======================
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔒 金融431考研记录")
            st.markdown("##### 一步一步重头来！ 🌟")
            username = st.text_input("账号")
            password = st.text_input("密码", type="password")

            CORRECT_USER = "kaoyan"
            CORRECT_PWD = "2026"
            if st.button("登录", use_container_width=True):
                if username == CORRECT_USER and password == CORRECT_PWD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("账号或密码错误，请重试！")
        st.stop()


# ====================== 配置区域 ======================
KAOYAN_DATE = date(2026, 12, 26)
DAILY_TARGET_HOURS = 8.0

SUBJECT_TOTAL_TARGET = {
    "政治": 200, "英语一": 250, "数学三": 400,
    "货币银行学": 300, "国际金融学": 250, "公司理财": 350, "投资学": 200
}
SUBJECT_LIST = list(SUBJECT_TOTAL_TARGET.keys())

# ====================== 云端数据库连接 ======================
conn = st.connection("kaoyan_db", type="sql")

TABLE_DAILY = "daily_record"
TABLE_WEEKLY_GOAL = "weekly_goal"
TABLE_WEEKLY_TARGET = "weekly_target"
TABLE_DAILY_PLAN = "daily_plan"


# ---------------------- 数据读写函数（云端升级版 + 空表保护） ----------------------
def load_data(table_name):
    """从云端数据库拉取数据，直接转为 Pandas DataFrame"""
    try:
        df = conn.query(f"SELECT * FROM {table_name}", ttl=0)
        return df
    except Exception:
        # 如果表不存在，返回一个空的 DataFrame
        return pd.DataFrame()


def save_data(df, table_name):
    """把最新的 DataFrame 推送到云端数据库"""
    try:
        df.to_sql(table_name, con=conn.engine, if_exists="replace", index=False)
    except Exception as e:
        st.error(f"同步到云端失败，请检查网络或配置: {e}")


def load_daily():
    df = load_data(TABLE_DAILY)
    return df if not df.empty else pd.DataFrame(columns=["日期", "科目", "学习时长(小时)", "学习笔记"])


def save_daily(df): save_data(df, TABLE_DAILY)


def load_weekly_goal():
    df = load_data(TABLE_WEEKLY_GOAL)
    return df if not df.empty else pd.DataFrame(columns=["周数", "开始日期", "结束日期", "学习目标", "完成状态"])


def save_weekly_goal(df): save_data(df, TABLE_WEEKLY_GOAL)


def load_weekly_subject_target():
    df = load_data(TABLE_WEEKLY_TARGET)
    return df if not df.empty else pd.DataFrame(columns=["周数", "开始日期", "结束日期", "科目", "周计划时长(小时)"])


def save_weekly_subject_target(df): save_data(df, TABLE_WEEKLY_TARGET)


def load_daily_plan():
    df = load_data(TABLE_DAILY_PLAN)
    if df.empty:
        return pd.DataFrame(columns=["日期", "任务内容", "科目", "计划时长(小时)", "实际时长(小时)", "完成状态"])
    if "实际时长(小时)" not in df.columns:
        df["实际时长(小时)"] = 0.0
        save_daily_plan(df)
    return df


def save_daily_plan(df): save_data(df, TABLE_DAILY_PLAN)


# ---------------------- 通用辅助函数 ----------------------
def get_countdown():
    return (KAOYAN_DATE - date.today()).days


def get_week_range(input_date=None):
    if input_date is None: input_date = date.today()
    start = input_date - timedelta(days=input_date.weekday())
    return start, start + timedelta(days=6)


def get_week_label(start, end):
    return f"{start} 至 {end}"


def get_all_week_list():
    df_target = load_weekly_subject_target()
    if df_target.empty:
        start, end = get_week_range()
        return [get_week_label(start, end)]
    week_list = df_target["周数"].unique().tolist()
    week_list.sort(reverse=True)
    return week_list


# ====================== 主程序 ======================
def main():
    check_login()
    st.set_page_config(page_title="金融431专属记录", page_icon="📊", layout="wide")

    countdown = get_countdown()
    today = date.today()
    current_week_start, current_week_end = get_week_range()
    current_week_label = get_week_label(current_week_start, current_week_end)
    all_week_list = get_all_week_list()

    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("📊 金融431二战考研专属记录系统")
    with col_logout:
        st.write("")
        if st.button("🚪 退出登录"):
            st.session_state.logged_in = False
            st.rerun()

    st.metric(label="⏳ 距离2026考研仅剩", value=f"{countdown} 天", delta="全力以赴，不留遗憾！")
    start_prepare = date(2024, 4, 1)
    total_days = (KAOYAN_DATE - start_prepare).days
    passed_days = (today - start_prepare).days
    progress_val = min(max(passed_days / total_days, 0.0), 1.0) if total_days > 0 else 0
    st.progress(progress_val, text="考研时间轴进度")
    st.markdown("---")

    st.sidebar.markdown("### 导航菜单")
    menu = st.sidebar.radio("功能导航", [
        "📈 今日看板",
        "📝 每日打卡",
        "📋 每日计划",
        "📊 任务可视化看板",
        "🎯 周度目标与计划",
        "💾 数据导出"
    ], label_visibility="collapsed")

    # ====================== 1. 今日看板 ======================
    if menu == "📈 今日看板":
        st.header("📋 今日学习看板")

        df_daily = load_daily()
        df_plan = load_daily_plan()

        today_records = df_daily[
            pd.to_datetime(df_daily["日期"]).dt.date == today].copy() if not df_daily.empty else pd.DataFrame()
        today_plan = df_plan[
            pd.to_datetime(df_plan["日期"]).dt.date == today].copy() if not df_plan.empty else pd.DataFrame()

        today_hours = today_records["学习时长(小时)"].sum() if not today_records.empty else 0
        delta_hours = today_hours - DAILY_TARGET_HOURS

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⏱️ 今日打卡总时长", f"{today_hours:.1f} 小时",
                      f"{delta_hours:.1f} 小时" if delta_hours != 0 else "已达标！",
                      delta_color="normal" if delta_hours > 0 else "off")
        with col2:
            st.metric("🎯 每日预设目标", f"{DAILY_TARGET_HOURS} 小时")
        with col3:
            plan_count = len(today_plan)
            finished_plan_count = len(today_plan[today_plan["完成状态"] == "已完成"]) if not today_plan.empty else 0
            st.metric("✅ 计划任务完成度", f"{finished_plan_count} / {plan_count}")

        st.markdown("---")

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.subheader("📌 今日计划执行追踪")
            if not today_plan.empty:
                for idx, row in today_plan.iterrows():
                    with st.container(border=True):
                        plan_h = row['计划时长(小时)']
                        actual_h = row.get('实际时长(小时)', 0.0)

                        task_col, stat_col = st.columns([3, 1])
                        with task_col:
                            checked = st.checkbox(
                                f"**{row['科目']}**: {row['任务内容']}",
                                value=(row["完成状态"] == "已完成"),
                                key=f"plan_{idx}"
                            )
                        with stat_col:
                            st.caption(f"{actual_h:.1f} / {plan_h:.1f} h")

                        prog = min(actual_h / plan_h, 1.0) if plan_h > 0 else 0
                        st.progress(prog)

                        if checked and row["完成状态"] == "未完成":
                            df_plan.loc[idx, "完成状态"] = "已完成"
                            save_daily_plan(df_plan)
                            st.toast(f"太棒了！完成了：{row['任务内容']}")
                            st.rerun()
                        elif not checked and row["完成状态"] == "已完成":
                            df_plan.loc[idx, "完成状态"] = "未完成"
                            save_daily_plan(df_plan)
                            st.rerun()
            else:
                st.info("🍃 今天还没有计划任务，去「每日计划」页面添加吧。")

            with st.expander("➕ 快速添加今日任务"):
                with st.form("quick_plan_form"):
                    quick_task = st.text_input("任务内容", placeholder="例如：背50个单词")
                    quick_subject = st.selectbox("科目", SUBJECT_LIST)
                    quick_hours = st.number_input("计划时长(小时)", 0.0, 24.0, 1.0, 0.5)
                    if st.form_submit_button("添加"):
                        if quick_task:
                            new_row = pd.DataFrame(
                                [[str(today), quick_task, quick_subject, quick_hours, 0.0, "未完成"]],
                                columns=df_plan.columns)
                            df_plan = pd.concat([df_plan, new_row], ignore_index=True)
                            save_daily_plan(df_plan)
                            st.toast("任务已添加！")
                            st.rerun()

        with col_right:
            st.subheader("📝 今日实际打卡明细")
            if not today_records.empty:
                for idx, row in today_records.iterrows():
                    with st.container(border=True):
                        col_content, col_del = st.columns([0.9, 0.1])
                        with col_content:
                            st.markdown(f"**{row['科目']}**：`{row['学习时长(小时)']} 小时`")
                            if pd.notna(row["学习笔记"]) and str(row["学习笔记"]).strip():
                                st.caption(f"📖 笔记/复盘：{row['学习笔记']}")
                        with col_del:
                            if st.button("🗑️", key=f"del_today_{idx}", help="删除此记录"):
                                df_daily = df_daily.drop(idx)
                                save_daily(df_daily)
                                st.toast("已删除该条打卡记录")
                                st.rerun()
            else:
                st.info("📭 今天还没有打卡记录哦，赶紧去学习吧！")

    # ====================== 2. 每日打卡 ======================
    elif menu == "📝 每日打卡":
        st.header("📝 学习打卡站")

        df_daily = load_daily()
        df_plan = load_daily_plan()

        if not df_plan.empty:
            today_tasks = df_plan[pd.to_datetime(df_plan["日期"]).dt.date == today]
            task_options = ["不关联计划"] + [f"{row['任务内容']} ({row['科目']})" for _, row in today_tasks.iterrows()]
        else:
            task_options = ["不关联计划"]

        with st.form("daily_form", border=True):
            col1, col2 = st.columns(2)
            with col1:
                record_date = st.date_input("🗓️ 日期", value=today)
            with col2:
                subject = st.selectbox("📚 科目", SUBJECT_LIST)

            hours = st.number_input("⏱️ 本次学习时长（小时）", 0.0, 24.0, step=0.5, value=1.0)
            notes = st.text_area("📝 今日复盘 / 笔记", placeholder="记录今天学了什么，有什么收获，遇到了什么困难...")
            linked_task = st.selectbox("🔗 关联今日计划（实际时长将自动累加）", task_options)

            submit = st.form_submit_button("🚀 提交打卡！", use_container_width=True)

            if submit:
                if hours <= 0:
                    st.warning("请输入有效的学习时长！")
                else:
                    new_row = pd.DataFrame([[str(record_date), subject, hours, notes]], columns=df_daily.columns)
                    df_daily = pd.concat([df_daily, new_row], ignore_index=True)
                    save_daily(df_daily)

                    if linked_task != "不关联计划":
                        task_desc, task_subject = linked_task.rsplit(" (", 1)
                        task_subject = task_subject.rstrip(")")
                        mask = (pd.to_datetime(df_plan["日期"]).dt.date == today) & (
                                    df_plan["任务内容"] == task_desc) & (df_plan["科目"] == task_subject)

                        if not df_plan[mask].empty:
                            current_actual = df_plan.loc[mask, "实际时长(小时)"].values[0]
                            planned_hours = df_plan.loc[mask, "计划时长(小时)"].values[0]
                            new_actual = current_actual + hours
                            df_plan.loc[mask, "实际时长(小时)"] = new_actual

                            if new_actual >= planned_hours and df_plan.loc[mask, "完成状态"].values[0] == "未完成":
                                df_plan.loc[mask, "完成状态"] = "已完成"
                                st.balloons()
                            save_daily_plan(df_plan)

                    st.success("🎉 打卡成功！进度已同步至今日看板！")
                    st.rerun()

    # ====================== 3. 每日计划 ======================
    elif menu == "📋 每日计划":
        st.header("📋 每日计划管理")

        df_plan = load_daily_plan()
        selected_date = st.date_input("📅 选择你要规划的日期", value=today)

        with st.form("add_plan_form", border=True):
            st.markdown("#### ➕ 添加新任务")
            col1, col2, col3 = st.columns([3, 2, 1.5])
            with col1:
                task_content = st.text_input("任务内容", placeholder="例如：做完数学三真题一套")
            with col2:
                task_subject = st.selectbox("科目", SUBJECT_LIST)
            with col3:
                task_hours = st.number_input("计划时长(h)", 0.0, 24.0, 1.0, 0.5)

            if st.form_submit_button("添加任务", use_container_width=True):
                if task_content:
                    new_row = pd.DataFrame(
                        [[str(selected_date), task_content, task_subject, task_hours, 0.0, "未完成"]],
                        columns=df_plan.columns)
                    df_plan = pd.concat([df_plan, new_row], ignore_index=True)
                    save_daily_plan(df_plan)
                    st.toast("任务添加成功！")
                    st.rerun()
                else:
                    st.warning("任务内容不能为空哦！")

        st.markdown("---")
        if not df_plan.empty:
            day_plan = df_plan[pd.to_datetime(df_plan["日期"]).dt.date == selected_date]
            if not day_plan.empty:
                st.subheader(f"✨ {selected_date} 的计划清单")
                for idx, row in day_plan.iterrows():
                    col1, col2, col3 = st.columns([5, 3, 1])
                    with col1:
                        status_emoji = "✅" if row["完成状态"] == "已完成" else "⏳"
                        st.markdown(f"{status_emoji} **{row['任务内容']}**")
                    with col2:
                        actual = row.get('实际时长(小时)', 0.0)
                        st.caption(f"{row['科目']} | 进度：{actual:.1f}h / 计划：{row['计划时长(小时)']}h")
                    with col3:
                        if st.button("🗑️ 删", key=f"del_plan_{idx}"):
                            df_plan = df_plan.drop(idx)
                            save_daily_plan(df_plan)
                            st.rerun()
            else:
                st.info(f"🍃 {selected_date} 暂无计划任务。")

    # ====================== 4. 可视化看板 ======================
    elif menu == "📊 任务可视化看板":
        st.header("📊 任务大盘可视化")
        selected_week = st.selectbox("切换查看周数", all_week_list, index=0)
        selected_week_start, selected_week_end = map(date.fromisoformat, selected_week.split(" 至 "))
        st.markdown("---")

        df_daily = load_daily()
        df_plan = load_daily_plan()
        df_weekly_target = load_weekly_subject_target()

        week_daily_data = df_daily[(pd.to_datetime(df_daily["日期"]).dt.date >= selected_week_start) & (pd.to_datetime(
            df_daily["日期"]).dt.date <= selected_week_end)] if not df_daily.empty else pd.DataFrame()
        week_plan_data = df_plan[(pd.to_datetime(df_plan["日期"]).dt.date >= selected_week_start) & (pd.to_datetime(
            df_plan["日期"]).dt.date <= selected_week_end)] if not df_plan.empty else pd.DataFrame()
        week_subject_target = df_weekly_target[df_weekly_target["周数"] == selected_week]

        st.subheader("🔥 每日任务落地执行力")
        st.caption("分析：对比你每天写下的『每日计划分配总时长』与『实际通过打卡落地的时长』")
        if not week_plan_data.empty:
            week_plan_data["日期"] = pd.to_datetime(week_plan_data["日期"]).dt.date
            daily_execution = week_plan_data.groupby("日期").agg(
                计划总时长=("计划时长(小时)", "sum"),
                实际完成时长=("实际时长(小时)", "sum")
            ).reset_index()

            date_range = [selected_week_start + timedelta(days=i) for i in range(7)]
            daily_execution = pd.merge(pd.DataFrame({"日期": date_range}), daily_execution, on="日期",
                                       how="left").fillna(0)
            daily_execution["日期"] = daily_execution["日期"].astype(str)

            st.bar_chart(daily_execution.set_index("日期")[["计划总时长", "实际完成时长"]],
                         color=["#A9A9A9", "#00BFFF"], height=300)

            total_plan_h = daily_execution["计划总时长"].sum()
            total_actual_h = daily_execution["实际完成时长"].sum()
            exec_rate = (total_actual_h / total_plan_h * 100) if total_plan_h > 0 else 0

            col_exec1, col_exec2, col_exec3 = st.columns(3)
            col_exec1.metric("本周分配计划总计", f"{total_plan_h:.1f} h")
            col_exec2.metric("本周实际落地总计", f"{total_actual_h:.1f} h")
            col_exec3.metric("本周计划执行力", f"{exec_rate:.1f}%")
        else:
            st.info("本周暂无每日计划记录，无法生成执行力分析。")

        st.markdown("---")

        st.subheader("📚 各科周度计划宏观完成进度")
        if week_subject_target.empty:
            st.warning("⚠️ 当前周还未设置科目宏观计划时长，请去左侧菜单「🎯 周度目标与计划」中设置！")
        else:
            week_subject_actual = week_daily_data.groupby("科目")[
                "学习时长(小时)"].sum().reset_index() if not week_daily_data.empty else pd.DataFrame(
                columns=["科目", "学习时长(小时)"])
            subject_detail = pd.merge(week_subject_target, week_subject_actual, on="科目", how="left").fillna(0)
            subject_detail["周完成率"] = (
                        subject_detail["学习时长(小时)"] / subject_detail["周计划时长(小时)"] * 100).round(1)

            total_subject_actual = df_daily.groupby("科目")[
                "学习时长(小时)"].sum().reset_index() if not df_daily.empty else pd.DataFrame(
                columns=["科目", "学习时长(小时)"])
            subject_detail = pd.merge(subject_detail, total_subject_actual, on="科目", how="left",
                                      suffixes=("", "_累计")).fillna(0)
            subject_detail["总目标时长"] = subject_detail["科目"].map(SUBJECT_TOTAL_TARGET)
            subject_detail["总目标完成率"] = (
                        subject_detail["学习时长(小时)_累计"] / subject_detail["总目标时长"] * 100).round(1)

            subject_detail_show = subject_detail.rename(columns={
                "周计划时长(小时)": "周目标(h)", "学习时长(小时)": "本周打卡(h)",
                "学习时长(小时)_累计": "累计打卡(h)", "总目标时长": "总目标(h)"
            })[["科目", "周目标(h)", "本周打卡(h)", "周完成率", "累计打卡(h)", "总目标(h)", "总目标完成率"]]

            col_table, col_chart = st.columns([1.2, 1])
            with col_table:
                def highlight_progress(row):
                    if row["周完成率"] < 100:
                        return ['background-color: rgba(255, 99, 71, 0.2)'] * len(row)
                    elif row["周完成率"] >= 100:
                        return ['background-color: rgba(60, 179, 113, 0.2)'] * len(row)
                    return [''] * len(row)

                st.dataframe(subject_detail_show.style.apply(highlight_progress, axis=1), use_container_width=True,
                             hide_index=True)
            with col_chart:
                chart_data = subject_detail[["科目", "周计划时长(小时)", "学习时长(小时)"]].set_index("科目")
                chart_data.columns = ["宏观目标规划", "实际打卡落地"]
                st.bar_chart(chart_data, horizontal=True)

    # ====================== 5. 周度目标与计划 ======================
    elif menu == "🎯 周度目标与计划":
        st.header("🎯 本周作战指挥部")
        st.caption(f"当前配置周度区间：**{current_week_label}**")
        st.markdown("---")

        tab_goal, tab_time = st.tabs(["🚩 本周核心任务 (定性)", "⏱️ 各科时长分配 (定量)"])

        with tab_goal:
            df_goal = load_weekly_goal()
            current_week_goals = df_goal[df_goal["周数"] == current_week_label] if not df_goal.empty else pd.DataFrame()

            with st.form("weekly_goal_form", border=True):
                new_goal = st.text_input("🎯 立下本周的 Flag", placeholder="例如：看完公司理财第5-8章并完成课后题...")
                if st.form_submit_button("➕ 添加任务") and new_goal:
                    new_row = pd.DataFrame(
                        [[current_week_label, str(current_week_start), str(current_week_end), new_goal, "未完成"]],
                        columns=df_goal.columns)
                    df_goal = pd.concat([df_goal, new_row], ignore_index=True)
                    save_weekly_goal(df_goal)
                    st.toast("新 Flag 已立，冲冲冲！")
                    st.rerun()

            if not current_week_goals.empty:
                st.subheader("清单列表")
                for idx, row in current_week_goals.iterrows():
                    with st.container(border=True):
                        col1, col2 = st.columns([8, 2])
                        with col1:
                            if row["完成状态"] == "已完成":
                                st.markdown(f"~~✅ {row['学习目标']}~~")
                            else:
                                st.markdown(f"🔥 **{row['学习目标']}**")
                        with col2:
                            action_col1, action_col2 = st.columns(2)
                            with action_col1:
                                if row["完成状态"] == "未完成":
                                    if st.button("完成", key=f"finish_goal_{idx}", help="标记为完成"):
                                        df_goal.loc[idx, "完成状态"] = "已完成"
                                        save_weekly_goal(df_goal)
                                        st.balloons()
                                        st.rerun()
                            with action_col2:
                                if st.button("🗑️", key=f"del_goal_{idx}", help="删除任务"):
                                    df_goal = df_goal.drop(idx)
                                    save_weekly_goal(df_goal)
                                    st.rerun()
            else:
                st.info("本周还没有立下具体任务 Flag 呢，快去规划一下吧。")

        with tab_time:
            st.info("💡 提示：在这里给每周的每个科目分配预期时间，看板中的『达成率』会根据这里的数据进行计算。")

            if st.button("⚡ 一键克隆上周的时长分配", use_container_width=True):
                last_week_start = current_week_start - timedelta(days=7)
                last_week_label = get_week_label(last_week_start, last_week_start + timedelta(days=6))
                df_target = load_weekly_subject_target()
                last_week_target = df_target[
                    df_target["周数"] == last_week_label] if not df_target.empty else pd.DataFrame()

                if not last_week_target.empty:
                    df_target = df_target[df_target["周数"] != current_week_label]
                    last_week_target["周数"] = current_week_label
                    last_week_target["开始日期"] = str(current_week_start)
                    last_week_target["结束日期"] = str(current_week_end)
                    df_target = pd.concat([df_target, last_week_target], ignore_index=True)
                    save_weekly_subject_target(df_target)
                    st.success("✅ 已成功复制上周的时长分配！")
                    st.rerun()
                else:
                    st.warning("⚠️ 上周你并没有设置时长分配，无法克隆！")

            df_target = load_weekly_subject_target()
            current_target = df_target[
                df_target["周数"] == current_week_label] if not df_target.empty else pd.DataFrame()

            with st.form("subject_target_form", border=True):
                st.subheader("⏱️ 分配各科复习时长 (小时)")
                target_data = {}
                cols = st.columns(3)
                for idx, subject in enumerate(SUBJECT_LIST):
                    default_value = 0.0
                    if not current_target.empty and subject in current_target["科目"].values:
                        default_value = float(
                            current_target[current_target["科目"] == subject]["周计划时长(小时)"].values[0])

                    with cols[idx % 3]:
                        target_data[subject] = st.number_input(f"{subject}", 0.0, 100.0, default_value, 0.5)

                if st.form_submit_button("✅ 保存本周时长目标", use_container_width=True):
                    df_target = df_target[
                        df_target["周数"] != current_week_label] if not df_target.empty else pd.DataFrame(
                        columns=["周数", "开始日期", "结束日期", "科目", "周计划时长(小时)"])
                    new_rows = [[current_week_label, str(current_week_start), str(current_week_end), subject, hours]
                                for subject, hours in target_data.items() if hours > 0]

                    if new_rows:
                        new_df = pd.DataFrame(new_rows, columns=df_target.columns)
                        df_target = pd.concat([df_target, new_df], ignore_index=True)
                        save_weekly_subject_target(df_target)
                        st.toast("🎉 时长目标已更新，看板数据已同步！")
                        st.rerun()
                    else:
                        st.warning("请至少为一个科目设置大于 0 的时间。")

    # ====================== 6. 数据导出 ======================
    elif menu == "💾 数据导出":
        st.header("💾 数据沉淀与导出")
        st.caption("定期备份你的考研汗水结晶 💎")
        tabs = st.tabs(["每日打卡明细", "每日计划", "周度科目目标", "周度大目标"])
        files = [
            (tabs[0], load_daily(), "打卡"),
            (tabs[1], load_daily_plan(), "每日计划"),
            (tabs[2], load_weekly_subject_target(), "周度科目目标"),
            (tabs[3], load_weekly_goal(), "周度大目标")
        ]

        for tab, df, name in files:
            with tab:
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    st.download_button(f"📥 下载{name}数据 (CSV)", df.to_csv(index=False, encoding="utf-8-sig"),
                                       f"考研{name}_{date.today()}.csv")
                else:
                    st.info(f"暂无{name}数据。")


if __name__ == "__main__":
    main()
