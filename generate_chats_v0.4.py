"""
Chat generation module for creating realistic chat data.
"""
import os
import uuid
import random
import string
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

from generator_config import *

@dataclass
class Exhibit:
    """Represents an evidence exhibit"""
    uuid: str
    case_id: str
    exhibit_number: int
    police_number: str
    extraction_date: datetime  # normalized to NZT
    name: str

@dataclass
class Participant:
    """Represents a chat participant"""
    name: str  # real name
    alias: str  # platform name
    platform: str  # platform the chat is from
    avatars: Dict  # resolvable file path
    uuid: str  # organizational identifier
    color: str  # hex code
    style_id: int  # style identifier

@dataclass
class Attachment:
    """Represents a message attachment"""
    uuid: str
    type: str  # [image, video, audio, link, file]
    file_name: str
    file_location: str
    message_uuid: str
    sender_uuid: str

@dataclass
class Message:
    """Represents a chat message"""
    sender_uuid: str
    uuid: str
    has_attachment: bool
    send_datetime: datetime
    sent_status: bool
    text: str
    delivered_datetime: Optional[datetime]
    delivered_status: bool
    read_datetime: Optional[datetime]
    read_status: bool
    deleted_datetime: Optional[datetime]
    deleted_status: bool
    platform_name: str
    exhibit_uuid: str

@dataclass
class CaseData:
    """Represents case metadata"""
    file_number: str
    case_number: str
    operation_name: str
    start_date: datetime
    end_date: datetime
    exhibits_used: List[str]
    notes: str = ""

class DateTimeGenerator:
    """Handles generation of datetime ranges and sequences"""
    
    @staticmethod
    def random_datetime(start: datetime, end: datetime) -> datetime:
        """Generate random datetime between start and end"""
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)

    @staticmethod
    def generate_datetime_range() -> Tuple[datetime, datetime]:
        """Generate random start/end datetime pair within 2023-2024"""
        start_range = datetime(2023, 1, 1)
        end_range = datetime(2024, 12, 31, 23, 59, 59)
        
        start = DateTimeGenerator.random_datetime(start_range, end_range)
        end = DateTimeGenerator.random_datetime(start, end_range)
        
        return start, end 

class ChatBuilder:
    """Handles assembly and output of complete chat data"""
    
    def __init__(self, params: Optional[Dict] = None):
        self.save_time = datetime.now().strftime('%Y%m%d%H%M%S')
        self.save_root = "generated_chats"
        
        if not os.path.exists(self.save_root):
            os.makedirs(self.save_root)

        self.platform = None
        self.participants = {}
        self.exhibits = {}
        self.attachments = []
        self.messages = []
        self.case_data = None
        
        # Initialize chat data
        self.initialize_chat(params)
        
    def initialize_chat(self, params: Optional[Dict] = None):
        """Initialize all chat components"""
        params = params or {}  # Convert None to empty dict
        
        # Set platform
        self.platform = params.get('platform', random.choice(PLATFORMS))
        print(f'Chat Platform: {self.platform}')
        
        # Generate participants
        self._generate_participants(params)
        print(f'Chat is between {len(self.participants)} parties: {", ".join(p.alias for p in self.participants.values())}')
        
        # Generate case data
        self._generate_case_data(params)
        
        # Generate exhibits
        self._generate_exhibits(params)
        print(f'Chat has {len(self.exhibits)} exhibits: {", ".join(e.name for e in self.exhibits.values())}')
        
        # Generate messages
        self._generate_messages(params)
        print(f'Chat has {len(self.messages)} messages\n')

    def _generate_participants(self, params: Optional[Dict] = None):
        """Generate chat participants"""
        if not params or "participants" not in params:
            num_participants = random.randint(2, MAX_PARTICIPANTS)
            style_ids = ParticipantGenerator.generate_distant_style_ids(num_participants)
            
            self.participants = {
                str(uuid.uuid4()): ParticipantGenerator.generate_participant(style_id)
                for style_id in style_ids
            }
        else:
            self.participants = params['participants']

    def _generate_case_data(self, params: Optional[Dict] = None):
        """Generate case metadata"""
        if not params or 'case_data' not in params:
            start_date, end_date = DateTimeGenerator.generate_datetime_range()
            self.case_data = CaseData(
                file_number=f"{random.randint(230000, 240000)}/{random.randint(1000, 9999)}",
                case_number=f"HTCG{random.randint(24000, 24400)}",
                operation_name=random.choice(OPERATION_NAMES),
                start_date=start_date,
                end_date=end_date,
                exhibits_used=[],
                notes=""
            )
        else:
            self.case_data = params['case_data']

    def _generate_exhibits(self, params: Optional[Dict] = None):
        """Generate exhibits"""
        if not params or "exhibits" not in params:
            for _ in range(len(self.participants)):
                exhibit = ExhibitGenerator.generate_exhibit(self.case_data)

                self.exhibits[exhibit.uuid] = exhibit
                self.case_data.exhibits_used.append(exhibit.name)
        else:
            self.exhibits = params['exhibits']

    def _generate_messages(self, params: Optional[Dict] = None):
        """Generate messages and attachments"""
        if not params or "messages" not in params:
            timeline = MessageGenerator.generate_message_timeline()
            
            for ref_dt in timeline:
                participant_uuid = random.choice(list(self.participants.keys()))
                exhibit_uuid = random.choice(list(self.exhibits.keys()))
                
                message, new_attachments = MessageGenerator.generate_message(
                    ref_dt, participant_uuid, exhibit_uuid, self.platform
                )
                
                self.messages.append(message)
                self.attachments.extend(new_attachments)
            
            # Sort messages by datetime
            self.messages.sort(key=lambda x: x.send_datetime)
        else:
            self.messages = params['messages']

    def save(self, filename: Optional[str] = None) -> str:
        """
        Save chat data to JSON file
        Args:
            filename: Optional custom filename. If None, generates automatic filename
        Returns:
            str: Path to saved file
        """
        if filename:
            # Use provided filename but ensure it's in the save directory
            save_path = os.path.join(self.save_root, filename)
        else:
            # Generate automatic filename
            chat_vars = f"{len(self.participants)}-pax_{len(self.messages)}-messages"
            save_path = os.path.join(self.save_root, f"{chat_vars}_{self.save_time}.json")
        
        # Convert to JSON structure
        chat_data = {
            "messages": {
                msg.send_datetime.isoformat(): asdict(msg) 
                for msg in self.messages
            },
            "attachments": {
                att.uuid: asdict(att) 
                for att in self.attachments
            },
            "participants": {
                p_uuid: asdict(participant)
                for p_uuid, participant in self.participants.items()
            },
            "exhibits": {
                ex.uuid: asdict(ex)
                for ex in self.exhibits.values()
            },
            "case_data": asdict(self.case_data)
        }
        
        # Convert datetime objects to ISO format strings
        for msg_data in chat_data["messages"].values():
            for dt_field in ['send_datetime', 'delivered_datetime', 'read_datetime', 'deleted_datetime']:
                if msg_data[dt_field]:
                    msg_data[dt_field] = msg_data[dt_field].isoformat()
                    
        for exhibit_data in chat_data["exhibits"].values():
            exhibit_data['extraction_date'] = exhibit_data['extraction_date'].isoformat()
            
        chat_data["case_data"]["start_date"] = chat_data["case_data"]["start_date"].isoformat()
        chat_data["case_data"]["end_date"] = chat_data["case_data"]["end_date"].isoformat()
        
        # Save to file
        with open(save_path, "w") as json_file:
            json.dump(chat_data, json_file, indent=4)
            print(f"Saved as JSON: {save_path}")
            
        return save_path

class ParticipantGenerator:
    """Handles generation of chat participants"""
    
    @staticmethod
    def generate_participant(style_id: Optional[int] = None) -> Participant:
        """Generate a single participant"""
        name, alias = ParticipantGenerator.generate_participant_name()
        
        # Ensure style_id is valid
        if style_id is None or style_id not in STYLE_ID_TO_COLOR:
            style_id = random.choice(list(STYLE_ID_TO_COLOR.keys()))
            
        # Generate avatar paths
        avatar_base = STYLE_ID_TO_AVATAR[style_id]
        avatars = {
            "left": avatar_base.replace(".png", "_l.png"),
            "right": avatar_base.replace(".png", "_r.png"),
            "center": avatar_base.replace(".png", "_c.png")  # Use center variant
        }

        return Participant(
            name=name,
            alias=alias,  # This will be used as display_name
            platform=random.choice(PLATFORMS),
            avatars=avatars,
            uuid=str(uuid.uuid4()),
            color=STYLE_ID_TO_COLOR[style_id],
            style_id=style_id
        )

    @staticmethod
    def generate_distant_style_ids(n: int) -> List[int]:
        """Generate n style IDs that are well-distributed"""
        available_ids = list(STYLE_ID_TO_COLOR.keys())
        if n > len(available_ids):
            raise ValueError(f"Cannot generate {n} unique style IDs - only {len(available_ids)} available")
        
        # Take every nth item to ensure good distribution
        step = len(available_ids) // n
        selected_indices = range(0, len(available_ids), step)
        return [available_ids[i] for i in selected_indices][:n]

    @staticmethod
    def generate_participant_name() -> Tuple[str, str]:
        """Generate random participant name and alias"""
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        alias = random.choice(PLATFORM_ALIAS_SEEDS)

        # Add random suffix to alias
        if random.choice([True, False]):
            if random.choice([True, False]):
                alias = f"{alias}_{random.randint(1, 1000)}"
            elif random.choice([True, False]):
                alias = f"__{alias}__"
            elif random.choice([True, False]):
                alias = f"{alias}{random.choice(ALIAS_SUFFIXES)}"

        return name, alias

class ExhibitGenerator:
    """Handles generation of exhibits"""

    @staticmethod
    def generate_exhibit(case_data: CaseData) -> Exhibit:
        """Generate a single exhibit"""
        
        
        exhibit_uuid = str(uuid.uuid4())
        police_id = ExhibitGenerator.generate_random_exhibit_ID()
        exhibit_number=random.randint(1, 20),
        extraction_date = datetime.now() - timedelta(
            days=random.randint(1, 5),
            hours=random.randint(1, 24),
            minutes=random.randint(1, 61),
            seconds=random.randint(1, 61),
            milliseconds=random.randint(1, 1001)
        )

    
        return Exhibit(
            uuid=exhibit_uuid,
            case_id=case_data.case_number,
            exhibit_number=exhibit_number,  # This should be managed better
            police_number=police_id,
            extraction_date=extraction_date,
            name=f"{case_data.case_number}_{exhibit_number[0]} ({police_id})"
        )

    @staticmethod
    def generate_random_exhibit_ID() -> str:
        """Generate random exhibit ID avoiding ambiguous characters"""
        allowed_chars = string.ascii_letters + string.digits
        allowed_chars = allowed_chars.replace('I', '').replace('l', '').replace('O', '').replace('0', '')
        return ''.join(random.choice(allowed_chars) for _ in range(6))

class MessageGenerator:
    """Handles generation of messages and message timelines"""
    
    @staticmethod
    def generate_message_timeline(start: Optional[datetime] = None,
                                end: Optional[datetime] = None,
                                message_count: Optional[int] = None) -> List[datetime]:
        """Generate timeline of message datetimes"""
        if not start or not end:
            start, end = DateTimeGenerator.generate_datetime_range()
        if not message_count:
            message_count = MessageGenerator.weighted_random_message_count()
            
        print(f"Generating message timeline - {message_count} messages between '{str(start)}' - '{str(end)}'\n")
        return MessageGenerator.generate_random_message_datetimes(start, end, message_count)

    @staticmethod
    def weighted_random_message_count() -> int:
        """Generate weighted random number of messages"""
        weighted_choice = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]

        if weighted_choice == 1:
            return random.choices([1, 2, 3, 4], weights=[0.3, 0.3, 0.2, 0.2], k=1)[0]
        
        # Generate normal distribution between 1 and 50
        normal_choice = int(random.gauss(25, 10))  # Mean = 25, Stddev = 10
        return max(1, min(50, normal_choice))

    @staticmethod
    def generate_random_message_datetimes(start: datetime, end: datetime, count: int) -> List[datetime]:
        """Generate list of random message datetimes"""
        time_difference = int((end - start).total_seconds())
        deltas = MessageGenerator.generate_random_points(time_difference, count)
        return [start + timedelta(seconds=delta) for delta in deltas]

    @staticmethod
    def generate_random_points(duration: int, count: int) -> List[int]:
        """Generate random time points for messages"""
        over_run_count = 10
        fuzz_range_min = 1
        fuzz_range_max = duration - (count + (over_run_count * 2))
        
        count_with_overrun = count + over_run_count
        mean_response_time = duration / count_with_overrun
        points = []
        
        for _ in range(count_with_overrun + over_run_count):
            fuzz = random.uniform(fuzz_range_min, fuzz_range_max)
            fuzzed_time = mean_response_time + fuzz if random.choice([True, False]) else max(mean_response_time - fuzz, 1)
            points.append(fuzzed_time)

        points = points[:count]
        
        if sum(points) > duration:
            return points
        return MessageGenerator.generate_random_points(duration, count)

    @staticmethod
    def generate_message(ref_dt: datetime, participant_uuid: str, 
                        exhibit_uuid: str, platform_name: str) -> Tuple[Message, List[Attachment]]:
        """Generate a single message with possible attachments"""
        message_uuid = str(uuid.uuid4())
        attachments = []
        
        # Determine if message has attachment
        has_attachment = random.random() < ATTACHMENT_LIKELIHOOD
        
        # Generate send datetime and status
        sent_status = random.random() < SENT_LIKELIHOOD
        send_datetime = ref_dt if sent_status else None
        
        # Generate delivery info
        delivered_status = sent_status and random.random() < DELIVERED_LIKELIHOOD
        delivered_datetime = None
        if delivered_status:
            min_delay, max_delay = MESSAGE_TIMING["DELIVERY_DELAY"]
            delivered_datetime = ref_dt + timedelta(seconds=random.randint(min_delay, max_delay))
        
        # Generate read info
        read_status = delivered_status and random.random() < READ_LIKELIHOOD
        read_datetime = None
        if read_status:
            min_delay, max_delay = MESSAGE_TIMING["READ_DELAY"]
            read_datetime = ref_dt + timedelta(seconds=random.randint(min_delay, max_delay))
        
        # Generate delete info
        deleted_status = random.random() < DELETED_LIKELIHOOD
        deleted_datetime = None
        if deleted_status:
            min_delay, max_delay = MESSAGE_TIMING["DELETE_DELAY"]
            deleted_datetime = ref_dt + timedelta(seconds=random.randint(min_delay, max_delay))
        
        # Generate attachments if needed
        if has_attachment:
            attachment_count = random.randint(1, 4)
            for _ in range(attachment_count):
                attachment_type = random.choice(list(ATTACHMENT_TYPES.keys()))
                attachments.append(
                    AttachmentGenerator.generate_attachment(
                        attachment_type, 
                        message_uuid, 
                        participant_uuid
                    )
                )
        
        message = Message(
            sender_uuid=participant_uuid,
            uuid=message_uuid,
            has_attachment=has_attachment,
            send_datetime=send_datetime,
            sent_status=sent_status,
            text=random.choice(MESSAGE_TEXTS),
            delivered_datetime=delivered_datetime,
            delivered_status=delivered_status,
            read_datetime=read_datetime,
            read_status=read_status,
            deleted_datetime=deleted_datetime,
            deleted_status=deleted_status,
            platform_name=platform_name,
            exhibit_uuid=exhibit_uuid
        )
        
        return message, attachments

class AttachmentGenerator:
    """Handles generation of message attachments"""
    
    @staticmethod
    def generate_attachment(attachment_type: str, message_uuid: str, sender_uuid: str) -> Attachment:
        """Generate a single attachment"""
        type_config = ATTACHMENT_TYPES[attachment_type]
        file_name = random.choice(type_config["files"])
        file_location = os.path.join(type_config["path"], file_name)
        
        return Attachment(
            uuid=str(uuid.uuid4()),
            type=attachment_type,
            file_name=file_name,
            file_location=file_location,
            message_uuid=message_uuid,
            sender_uuid=sender_uuid
        )

def main(filename: Optional[str] = None):
    """
    Generate a sample chat
    Args:
        filename: Optional output filename. If None, generates automatic filename
    """
    chat = ChatBuilder()
    chat.save(filename)

if __name__ == "__main__":
    import sys
    
    # Get filename from command line argument if provided
    output_filename = sys.argv[1] if len(sys.argv) > 1 else None

    if not output_filename:
        output_filename = "test.json"   
        
    main(output_filename) 