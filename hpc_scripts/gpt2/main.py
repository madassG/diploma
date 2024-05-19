from transformers import TextDataset, DataCollatorForLanguageModeling
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from transformers import Trainer, TrainingArguments
import torch

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

DATA_PATH = './data/{}'
MODEL_PATH = './base'
OUTPUT_DIR = './fine_tuned/'

if __name__ == '__main__':
    print("device: ", DEVICE)
    print("preparing tokenized and model")
    tokenizer = GPT2Tokenizer.from_pretrained(MODEL_PATH)
    print("tokenizer: ", tokenizer)
    model = GPT2LMHeadModel.from_pretrained(MODEL_PATH).to(DEVICE)
    print("model: ", model)
    print("loading data...")
    train_dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=DATA_PATH.format('code_instructions_train.txt'),
        block_size=128,
    )
    print("train dataset loaded...")
    validation_dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=DATA_PATH.format('code_instructions_validation.txt'),
        block_size=128,
    )
    print("validation dataset loaded...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        overwrite_output_dir=True,
        per_device_train_batch_size=12,
        num_train_epochs=5,
        save_steps=12000,
        save_strategy="steps",
    )
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    print("data collator loaded...")
    print("starting training...")
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
    )
    trainer.train()
    print("model fine-tuned successfully...")
    trainer.save_model()
    print("model saved successfully...")
