import const

import datasets
from transformers import TrainingArguments
from transformers import Trainer
from transformers import AutoTokenizer
from transformers import T5ForConditionalGeneration
from transformers import DataCollatorForSeq2Seq
import torch

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

tokenizer = AutoTokenizer.from_pretrained('./t5_small_tokenizer')
model = T5ForConditionalGeneration.from_pretrained('./t5_small', torch_dtype=torch.float16).to(DEVICE)


def preprocess_function(data_point):
    prompt = f"""You are a helpful, precise, detailed, and concise artificial intelligence
        assistant with a deep expertise in Python programming language.

        In this task, you are asked to read the problem description and return
        the software code in the python programming language. Please output
        only the code with comments.

        Generated answer have to be a piece of software that can run without errors.
        The generated answer is the cleanest and most efficient implementation.

        ### Problem:
        {data_point["instruction"]}

        ### Seed:
        {data_point["input"]}

        ### Solution:
        {data_point["output"]}{tokenizer.eos_token}"""

    inputs = tokenizer(
        prompt,
        truncation=True,
        max_length=const.MAX_LENGTH,
        padding=False,
        return_tensors=None,
    )
    inputs["labels"] = inputs["input_ids"].copy()

    return inputs


if __name__ == '__main__':
    print("Started")
    print("device: ", DEVICE)
    print("model: ", model)
    print("tokenizer: ", tokenizer)
    TRAIN_DATA = './dataset/github_train.csv'
    VAL_DATA = './dataset/github_val.csv'
    dataset = datasets.load_dataset('csv', data_files={
        'train': TRAIN_DATA, 'validation': VAL_DATA}, num_proc=8)
    print("Dataset loaded")
    tokenized_dataset = dataset.map(preprocess_function, num_proc=8)
    print("Dataset tokenized")

    training_args = TrainingArguments(
        f't5_small_finetuned',
        num_train_epochs=3,
        learning_rate=3e-4,
        per_device_train_batch_size=const.BATCH_SIZE,
        per_device_eval_batch_size=const.BATCH_SIZE,
        overwrite_output_dir=True,
        gradient_accumulation_steps=16,

        weight_decay=0.01,
        fp16=False,

        logging_dir='./logs',
        logging_steps=20,
        eval_steps=100,
        save_steps=100,
        evaluation_strategy='steps',

        load_best_model_at_end=True,
        group_by_length=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=DataCollatorForSeq2Seq(
            tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True
        ),
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["validation"],
    )

    print("Starting fine-tuning...")
    trainer.train()
    print("Model successfully fine-tuned")
    print("Saving fine-tuned-model")
    trainer.save_model('./t5_small_result_fine_tuned')
    print("Model saved successfully")
