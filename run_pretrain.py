import argparse
import os
import random

import torch
from torch.optim import Adam

from runner.pretrain_trainer import PreTrainer
from model.neural_apprentice import SmilesGenerator, SmilesGeneratorHandler
from util.smiles.dataset import load_dataset
from util.smiles.char_dict import SmilesCharDictionary


import neptune

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="pretrain", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    #parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="zinc")
    parser.add_argument("--dataset_path", type=str, default="./resource/data/zinc/train.txt")
    parser.add_argument("--max_smiles_length", type=int, default=80)
    parser.add_argument("--hidden_size", type=int, default=1024)
    parser.add_argument("--n_layers", type=int, default=3)
    parser.add_argument("--lstm_dropout", type=float, default=0.2)

    parser.add_argument("--learning_rate", type=float, default=1e-3)
    parser.add_argument("--num_epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=256)

    parser.add_argument("--save_dir", default="")

    args = parser.parse_args()

    device = torch.device(0)
    random.seed(0)

    neptune.init(project_qualified_name="",
                 api_token='',
                 )

    neptune.create_experiment(name="pretrain", params=vars(args))
    neptune.append_tag(args.dataset)


    char_dict = SmilesCharDictionary(dataset=args.dataset, max_smi_len=args.max_smiles_length)
    dataset = load_dataset(char_dict=char_dict, smi_path=args.dataset_path)

    input_size = max(char_dict.char_idx.values()) + 1
    generator = SmilesGenerator(
        input_size=input_size,
        hidden_size=args.hidden_size,
        output_size=input_size,
        n_layers=args.n_layers,
        lstm_dropout=args.lstm_dropout,
    )
    generator = generator.to(device)
    optimizer = Adam(params=generator.parameters(), lr=args.learning_rate)
    generator_handler = SmilesGeneratorHandler(
        model=generator, optimizer=optimizer, char_dict=char_dict, max_sampling_batch_size=0
    )

    trainer = PreTrainer(
        char_dict=char_dict,
        dataset=dataset,
        generator_handler=generator_handler,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        save_dir=args.save_dir,
        device=device,
    )

    trainer.train()
