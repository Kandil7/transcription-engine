#!/usr/bin/env python3
"""Script to populate the Arabic knowledge base for RAG corrections."""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.services.rag_service import rag_service


async def populate_arabic_kb():
    """Populate the Arabic knowledge base with sample correct transcripts."""

    # Sample correct Arabic transcripts (MSA and Egyptian dialect)
    arabic_documents = [
        # Modern Standard Arabic examples
        """
        مرحباً بكم في هذا البرنامج التعليمي. سنتحدث اليوم عن أهمية التكنولوجيا في التعليم.
        التكنولوجيا ساعدت في تحسين طرق التدريس وزيادة فعالية التعلم.
        يمكن للطلاب الآن الوصول إلى المواد التعليمية من أي مكان في العالم.
        هذا يفتح آفاقاً جديدة للتعليم المفتوح والمتاح للجميع.
        """,

        # Egyptian dialect examples
        """
        أهلاً وسهلاً فيكم يا جماعة. النهاردة هنتكلم عن الذكاء الاصطناعي وإزاي بيغير حياتنا.
        الذكاء الاصطناعي ده بيحل مشاكل كتير في مجالات مختلفة زي الطب والتعليم.
        في المستشفيات، بيستخدموا الذكاء الاصطناعي عشان يساعد الأطباء في التشخيص.
        في المدارس، بيحسن طرق التدريس ويخلي التعلم أكتر متعة للطلاب.
        """,

        # Technical content
        """
        الذكاء الاصطناعي هو فرع من فروع علم الحاسوب يهتم بتطوير آلات قادرة على أداء مهام تتطلب عادة ذكاء بشرياً.
        يشمل ذلك التعلم الآلي والتعلم العميق والمعالجة الطبيعية للغة.
        التعلم الآلي يعتمد على خوارزميات تستطيع التعلم من البيانات دون برمجة صريحة.
        التعلم العميق يستخدم شبكات عصبية اصطناعية متعددة الطبقات لمعالجة البيانات المعقدة.
        """,

        # Educational content
        """
        في هذا الدرس سنتعلم أساسيات البرمجة. البرمجة هي عملية كتابة التعليمات للحاسوب لتنفيذ مهام محددة.
        نبدأ بتعلم لغات البرمجة الأساسية مثل بايثون وجافا سكريبت.
        بايثون لغة برمجة سهلة التعلم وتستخدم في مجالات متعددة.
        جافا سكريبت تستخدم لتطوير مواقع الويب التفاعلية.
        المتغيرات هي حاويات لتخزين القيم في البرنامج.
        """
    ]

    try:
        print("Initializing RAG service...")
        await rag_service.initialize()

        print("Populating Arabic knowledge base...")
        await rag_service.index_arabic_knowledge_base(arabic_documents)

        print("✅ Knowledge base populated successfully!")
        print(f"Indexed {len(arabic_documents)} documents")

        # Check the collection
        stats = rag_service.get_collection_stats("arabic_kb")
        print(f"Collection stats: {stats}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(populate_arabic_kb())
    sys.exit(exit_code)