# app_nicegui/management_center.py
from nicegui import ui

# 使用更精确的导入路径
from app.services.person_service import person_service
from app.services.account_service import account_service
from app.schemas.person import PersonCreate
from app.schemas.account import AccountCreate
from app.core.database import get_session_local


def show_management_center_page():
    """渲染管理中心页面的所有UI元素"""
    ui.label("管理中心").classes("text-h4 q-ma-md")

    with ui.tabs().classes("w-full") as tabs:
        ui.tab(name="create_user", label="👤 创建新用户")
        ui.tab(name="add_account", label="💳 添加新账户")

    with ui.tab_panels(tabs, value="create_user").classes("w-full"):
        with ui.tab_panel("create_user"):
            with ui.card().classes("w-full"):
                ui.label("创建新的用户实体").classes("text-h6")

                name_input = ui.input(label="用户全名", placeholder="例如：张三")
                id_type_input = ui.input(label="证件类型 (可选)")
                id_number_input = ui.input(label="证件号码 (可选)")

                async def handle_create_user():
                    if not name_input.value:
                        ui.notify("“用户全名”是必填项。", type="warning")
                        return

                    session_local = get_session_local()
                    async with session_local() as session:
                        try:
                            person_data = PersonCreate(
                                full_name=name_input.value,
                                id_type=id_type_input.value or None,
                                id_number=id_number_input.value or None,
                            )
                            await person_service.create_person(
                                session, person_in=person_data
                            )
                            ui.notify(
                                f"🎉 用户 '{name_input.value}' 创建成功！",
                                type="positive",
                            )
                            name_input.value = ""
                            id_type_input.value = ""
                            id_number_input.value = ""
                        except Exception as e:
                            ui.notify(f"创建失败: {e}", type="negative")

                ui.button("创建用户", on_click=handle_create_user)

        with ui.tab_panel("add_account"):
            with ui.card().classes("w-full"):
                ui.label("为现有用户添加新的银行账户").classes("text-h6")

                person_options = {}
                person_select = ui.select(
                    options=person_options, label="选择用户"
                ).classes("w-full")

                async def load_persons():
                    session_local = get_session_local()
                    async with session_local() as session:
                        try:
                            all_persons = await person_service.get_all_persons(session)
                            person_options.clear()
                            for p in all_persons:
                                person_options[p.id] = p.full_name
                            person_select.update()
                        except Exception as e:
                            ui.notify(f"加载用户列表失败: {e}", type="negative")

                account_name_input = ui.input(
                    label="账户名称", placeholder="例如：招行工资卡"
                )
                account_number_input = ui.input(label="银行账号/卡号")
                account_type_input = ui.input(label="账户类型 (可选)")
                institution_input = ui.input(label="所属金融机构 (可选)")

                async def handle_add_account():
                    if not all(
                        [
                            person_select.value,
                            account_name_input.value,
                            account_number_input.value,
                        ]
                    ):
                        ui.notify(
                            "请先选择用户，并填写账户名称和账号。", type="warning"
                        )
                        return

                    # --- 【核心修复点】: 使用 assert 明确告知类型检查器 ---
                    owner_id = person_select.value
                    assert owner_id is not None, "Owner ID should not be None here."

                    session_local = get_session_local()
                    async with session_local() as session:
                        try:
                            account_data = AccountCreate(
                                account_name=account_name_input.value,
                                account_number=account_number_input.value,
                                account_type=account_type_input.value or None,
                                institution=institution_input.value or None,
                            )
                            await account_service.create_account(
                                session, owner_id=owner_id, account_in=account_data
                            )
                            ui.notify(
                                f"🎉 成功添加新账户 '{account_name_input.value}'！",
                                type="positive",
                            )
                            account_name_input.value = ""
                            account_number_input.value = ""
                            account_type_input.value = ""
                            institution_input.value = ""
                        except Exception as e:
                            ui.notify(f"添加账户失败: {e}", type="negative")

                ui.button("添加账户", on_click=handle_add_account)

                ui.timer(0.1, load_persons, once=True)
