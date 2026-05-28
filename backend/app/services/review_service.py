from datetime import date, timedelta

# 艾宾浩斯遗忘曲线间隔（天数）
REVIEW_INTERVALS = [1, 3, 7, 14, 30]


def get_next_review_date(review_count: int, is_correct: bool) -> tuple[date, str]:
    """
    根据复习次数和答题结果计算下次复习日期和掌握程度
    :param review_count: 当前复习次数（答题正确后更新）
    :param is_correct: 本次复习是否答对
    :return: (next_review_date, mastery)
    """
    today = date.today()

    if not is_correct:
        # 答错：重置复习周期
        next_review = today + timedelta(days=REVIEW_INTERVALS[0])
        return next_review, "unmastered"

    # 答对：进入下一个间隔
    new_count = review_count + 1

    if new_count >= len(REVIEW_INTERVALS):
        # 已完成所有复习周期，标记为已掌握
        next_review = today + timedelta(days=REVIEW_INTERVALS[-1])
        return next_review, "mastered"
    else:
        next_review = today + timedelta(days=REVIEW_INTERVALS[new_count - 1])
        mastery = "fuzzy" if new_count <= 2 else "mastered"
        return next_review, mastery


def get_initial_review_date() -> date:
    """新加入错题的初始复习日期（明天）"""
    return date.today() + timedelta(days=1)


def get_review_message(next_review: date, review_count: int, mastery: str, is_correct: bool) -> str:
    """生成复习结果提示信息"""
    if not is_correct:
        return f"❌ 答错了，加油！下次复习时间：明天"

    days_until = (next_review - date.today()).days
    if mastery == "mastered":
        return f"🎉 太棒了！已标记为已掌握，下次复习：{days_until}天后"
    elif days_until == 1:
        return f"✅ 答对了！下次复习时间：明天"
    else:
        return f"✅ 答对了！下次复习时间：{days_until}天后"
