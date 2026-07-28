from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.weak_topic import WeakTopic

RECOMMENDATION_TEMPLATES = {
    "Khóa chính": (
        "Khuyên đọc: Tài liệu Ràng buộc toàn vẹn trang 3-5.\n"
        "Hành động đề xuất:\n"
        "1. Xem lại định nghĩa tính duy nhất (Uniqueness) và tính không rỗng (Not Null) của Khóa chính.\n"
        "2. Tạo quiz trắc nghiệm 'Khóa chính' mức độ Easy để ôn tập lý thuyết.\n"
        "3. Xem slide bài giảng Chương 2 về các ví dụ thiết lập Khóa chính đơn và Khóa chính hợp phần."
    ),
    "Khóa ngoại": (
        "Khuyên đọc: Tài liệu Ràng buộc khóa ngoại trang 6-9.\n"
        "Hành động đề xuất:\n"
        "1. Đọc lại quy tắc tham chiếu (cascade, set null, restrict) khi cập nhật hoặc xóa dữ liệu khóa chính.\n"
        "2. Làm quiz trắc nghiệm 'Khóa ngoại' mức độ Medium.\n"
        "3. Vẽ thử sơ đồ liên kết bảng SinhVien (Maso) -> LopHoc (Malop) để hình dung rõ mối quan hệ."
    ),
    "SQL JOIN": (
        "Khuyên đọc: Tài liệu Truy vấn kết hợp bảng (SQL JOIN) trang 10-14.\n"
        "Hành động đề xuất:\n"
        "1. Vẽ sơ đồ Venn biểu thị INNER JOIN, LEFT JOIN, RIGHT JOIN và FULL JOIN.\n"
        "2. Thực hành truy vấn JOIN trên hệ cơ sở dữ liệu mẫu trong slide Chương 4.\n"
        "3. Tạo quiz 'SQL JOIN' với số lượng 5 câu hỏi để rèn luyện kỹ năng ghép bảng."
    ),
    "Chuẩn hóa cơ sở dữ liệu": (
        "Khuyên đọc: Tài liệu Chuẩn hóa cơ sở dữ liệu trang 15-22.\n"
        "Hành động đề xuất:\n"
        "1. Ôn lại định nghĩa Phụ thuộc hàm, khóa tối thiểu và các dạng chuẩn 1NF, 2NF, 3NF.\n"
        "2. Giải bài tập mẫu phân rã lược đồ quan hệ sang dạng chuẩn 3NF.\n"
        "3. Đọc lại phần slide bài giảng Chương 5 về các lỗi dị thường dữ liệu khi chưa chuẩn hóa."
    ),
    "ERD": (
        "Khuyên đọc: Tài liệu Thiết kế mô hình ERD trang 1-4.\n"
        "Hành động đề xuất:\n"
        "1. Học thuộc các ký hiệu thực thể (hình chữ nhật), thuộc tính (hình elip) và mối quan hệ (hình thoi).\n"
        "2. Tập vẽ sơ đồ ERD cho các bài toán kinh điển: Quản lý thư viện, Quản lý bán hàng.\n"
        "3. Tạo quiz 'ERD' để ôn tập cách xác định bản số (cardinality ratio)."
    ),
}

def get_recommendations(
    db: Session,
    user_id: int,
    course_id: int,
) -> list[dict[str, str]]:
    weak_topics = (
        db.query(WeakTopic)
        .filter(
            WeakTopic.user_id == user_id,
            WeakTopic.course_id == course_id,
            WeakTopic.status == "active",
        )
        .order_by(WeakTopic.created_at.desc())
        .all()
    )

    recommendations: list[dict[str, str]] = []
    for item in weak_topics:
        rec_text = RECOMMENDATION_TEMPLATES.get(
            item.topic,
            f"Bạn nên ôn lại chủ đề {item.topic}, đọc lại các đoạn tài liệu liên quan "
            "và làm quiz luyện tập để kiểm tra mức độ hiểu bài."
        )
        recommendations.append(
            {
                "topic": item.topic,
                "recommendation": rec_text,
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "topic": "Ôn tập chung",
                "recommendation": (
                    "Chưa phát hiện topic yếu rõ ràng. Bạn có thể tiếp tục hỏi chatbot "
                    "và làm quiz theo các chủ đề trọng tâm của môn học."
                ),
            }
        )

    return recommendations
