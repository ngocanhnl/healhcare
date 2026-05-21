"""Danh mục chuyên khoa dùng chung trong form tìm kiếm và hồ sơ bác sĩ."""

MEDICAL_SPECIALTIES: tuple[str, ...] = (
    "Nội tổng quát",
    "Ngoại tổng quát",
    "Tim mạch",
    "Thần kinh",
    "Da liễu",
    "Tai Mũi Họng",
    "Mắt",
    "Răng Hàm Mặt",
    "Sản phụ khoa",
    "Khoa nhi",
    "Chấn thương chỉnh hình",
    "Tiêu hóa",
    "Hô hấp",
    "Nội tiết",
    "Thận - Tiết niệu",
    "Ung bướu",
    "Dị ứng - Miễn dịch",
    "Tâm thần",
    "Phục hồi chức năng",
    "Y học cổ truyền",
)

MEDICAL_SPECIALTY_SET = frozenset(MEDICAL_SPECIALTIES)


def specialty_form_choices() -> list[tuple[str, str]]:
    return [(value, value) for value in MEDICAL_SPECIALTIES]


def specialty_search_choices() -> list[tuple[str, str]]:
    return [("", "Tất cả chuyên khoa"), *specialty_form_choices()]


def is_valid_medical_specialty(value: str | None) -> bool:
    return bool(value and value.strip() in MEDICAL_SPECIALTY_SET)
