from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.student import Student
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.textbook import Textbook
from app.services.max_bot_client import MaxBotClient


class ParentNotificationService:
    def __init__(self):
        self.max_bot = MaxBotClient()
    
    async def notify_issue_textbooks(self, student_id: int, textbook_ids: List[int], db: Session):
        """Уведомление родителей о выдаче учебников"""
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.parent_phone:
            return
        
        # Получаем информацию об учебниках
        textbooks = db.query(Textbook).filter(Textbook.id.in_(textbook_ids)).all()
        
        if not textbooks:
            return
        
        # Формируем список учебников
        textbook_list = []
        for textbook in textbooks:
            textbook_list.append(f"• {textbook.subject}: {textbook.title}")
        
        textbook_text = "\n".join(textbook_list)
        
        # Отправляем уведомление
        await self.max_bot.send_parent_notification(
            parent_phone=student.parent_phone,
            student_name=student.full_name,
            message_type="issue",
            textbook_list=textbook_text,
            total_count=len(textbooks)
        )
    
    async def notify_return_textbooks(self, student_id: int, textbook_ids: List[int], db: Session):
        """Уведомление родителей о возврате учебников"""
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.parent_phone:
            return
        
        # Получаем информацию об учебниках
        textbooks = db.query(Textbook).filter(Textbook.id.in_(textbook_ids)).all()
        
        if not textbooks:
            return
        
        # Формируем список учебников
        textbook_list = []
        for textbook in textbooks:
            textbook_list.append(f"• {textbook.subject}: {textbook.title}")
        
        textbook_text = "\n".join(textbook_list)
        
        # Отправляем уведомление
        await self.max_bot.send_parent_notification(
            parent_phone=student.parent_phone,
            student_name=student.full_name,
            message_type="return",
            textbook_list=textbook_text,
            total_count=len(textbooks)
        )
    
    async def notify_lost_textbook(self, student_id: int, textbook_id: int, db: Session):
        """Уведомление родителей об утере учебника"""
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.parent_phone:
            return
        
        textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
        if not textbook:
            return
        
        # Отправляем уведомление
        await self.max_bot.send_parent_notification(
            parent_phone=student.parent_phone,
            student_name=student.full_name,
            message_type="lost",
            textbook_name=f"{textbook.subject}: {textbook.title}",
            lost_date=datetime.utcnow().strftime("%d.%m.%Y")
        )
    
    async def notify_found_textbook(self, finder_student_id: int, textbook_id: int, db: Session):
        """Уведомление родителей о находке учебника"""
        finder_student = db.query(Student).filter(Student.id == finder_student_id).first()
        textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
        
        if not finder_student or not textbook:
            return
        
        # Находим владельца учебника
        active_transaction = db.query(Transaction).filter(
            Transaction.textbook_id == textbook_id,
            Transaction.transaction_type == TransactionType.ISSUE,
            Transaction.status == TransactionStatus.COMPLETED
        ).first()
        
        if not active_transaction:
            return
        
        owner_student = db.query(Student).filter(Student.id == active_transaction.student_id).first()
        if not owner_student or not owner_student.parent_phone:
            return
        
        # Отправляем уведомление владельцу
        await self.max_bot.send_parent_notification(
            parent_phone=owner_student.parent_phone,
            student_name=owner_student.full_name,
            message_type="found",
            textbook_name=f"{textbook.subject}: {textbook.title}",
            finder_name=finder_student.full_name
        )
    
    async def notify_bulk_issue_summary(self, grade: str, db: Session):
        """Уведомление родителей о массовой выдаче учебников в классе"""
        # Получаем всех учеников класса
        students = db.query(Student).filter(
            Student.grade == grade,
            Student.is_active == True
        ).all()
        
        for student in students:
            if not student.parent_phone:
                continue
            
            # Получаем активные учебники ученика
            active_transactions = db.query(Transaction).filter(
                Transaction.student_id == student.id,
                Transaction.transaction_type == TransactionType.ISSUE,
                Transaction.status == TransactionStatus.COMPLETED
            ).all()
            
            if not active_transactions:
                continue
            
            # Проверяем, есть ли возвраты
            active_textbooks = []
            for transaction in active_transactions:
                return_transaction = db.query(Transaction).filter(
                    Transaction.textbook_id == transaction.textbook_id,
                    Transaction.transaction_type == TransactionType.RETURN,
                    Transaction.status == TransactionStatus.COMPLETED
                ).first()
                
                if not return_transaction:
                    textbook = db.query(Textbook).filter(Textbook.id == transaction.textbook_id).first()
                    if textbook:
                        active_textbooks.append(f"• {textbook.subject}: {textbook.title}")
            
            if active_textbooks:
                textbook_text = "\n".join(active_textbooks)
                
                await self.max_bot.send_parent_notification(
                    parent_phone=student.parent_phone,
                    student_name=student.full_name,
                    message_type="bulk_issue_summary",
                    textbook_list=textbook_text,
                    total_count=len(active_textbooks)
                )
    
    async def notify_bulk_return_reminder(self, grade: str, db: Session):
        """Напоминание родителям о необходимости сдать учебники в конце года"""
        # Получаем всех учеников класса
        students = db.query(Student).filter(
            Student.grade == grade,
            Student.is_active == True
        ).all()
        
        for student in students:
            if not student.parent_phone:
                continue
            
            # Получаем активные учебники ученика
            active_transactions = db.query(Transaction).filter(
                Transaction.student_id == student.id,
                Transaction.transaction_type == TransactionType.ISSUE,
                Transaction.status == TransactionStatus.COMPLETED
            ).all()
            
            if not active_transactions:
                continue
            
            # Проверяем, есть ли возвраты
            not_returned_textbooks = []
            for transaction in active_transactions:
                return_transaction = db.query(Transaction).filter(
                    Transaction.textbook_id == transaction.textbook_id,
                    Transaction.transaction_type == TransactionType.RETURN,
                    Transaction.status == TransactionStatus.COMPLETED
                ).first()
                
                if not return_transaction:
                    textbook = db.query(Textbook).filter(Textbook.id == transaction.textbook_id).first()
                    if textbook:
                        not_returned_textbooks.append(f"• {textbook.subject}: {textbook.title}")
            
            if not_returned_textbooks:
                textbook_text = "\n".join(not_returned_textbooks)
                
                await self.max_bot.send_parent_notification(
                    parent_phone=student.parent_phone,
                    student_name=student.full_name,
                    message_type="return_reminder",
                    textbook_list=textbook_text,
                    total_count=len(not_returned_textbooks)
                )
    
    async def notify_damage_check_reminder(self, student_id: int, db: Session):
        """Напоминание родителям о необходимости проверить повреждения в течение недели"""
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.parent_phone:
            return
        
        # Получаем учебники, выданные в течение последней недели
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_transactions = db.query(Transaction).filter(
            Transaction.student_id == student_id,
            Transaction.transaction_type == TransactionType.ISSUE,
            Transaction.status == TransactionStatus.COMPLETED,
            Transaction.issued_at >= week_ago
        ).all()
        
        if recent_transactions:
            await self.max_bot.send_parent_notification(
                parent_phone=student.parent_phone,
                student_name=student.full_name,
                message_type="damage_check_reminder",
                textbook_count=len(recent_transactions),
                deadline_days=7
            ) 