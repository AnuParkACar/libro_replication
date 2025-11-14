"""
Model management for loading and caching HuggingFace models.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import json
from typing import Optional

class ModelManager:
    """Manages model loading, caching, and inference."""
    
    SUPPORTED_MODELS = {
        "starcoder2-3b": "bigcode/starcoder2-3b",
        "starcoder2-7b": "bigcode/starcoder2-7b",
        "codellama-7b": "codellama/CodeLlama-7b-hf",
        "deepseek-coder-7b": "deepseek-ai/deepseek-coder-7b-base-v1.5"
    }
    
    def __init__(self, model_key: str, cache_dir: Optional[str] = None):
        """
        Initialize model manager.
        
        Args:
            model_key: Key from SUPPORTED_MODELS
            cache_dir: Directory to cache models (for faster reloading)
        """
        if model_key not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model_key}")
        
        self.model_key = model_key
        self.model_name = self.SUPPORTED_MODELS[model_key]
        self.cache_dir = Path(cache_dir) if cache_dir else None
        
        self.model = None
        self.tokenizer = None
        
    def load(self):
        """Load model and tokenizer."""
        print(f"Loading {self.model_name}...")
        
        # Try to load from cache first
        if self.cache_dir and self.cache_dir.exists():
            try:
                print(f"  Loading from cache: {self.cache_dir}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.cache_dir)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.cache_dir,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
                print("  ✓ Loaded from cache")
                return
            except Exception as e:
                print(f"  Cache load failed: {e}")
        
        # Load from HuggingFace
        print(f"  Loading from HuggingFace: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Cache for next time
        if self.cache_dir:
            print(f"  Caching to: {self.cache_dir}")
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.model.save_pretrained(self.cache_dir)
            self.tokenizer.save_pretrained(self.cache_dir)
        
        print("  ✓ Model loaded")
    
    def generate(self, prompt: str, max_tokens: int = 256, 
                 temperature: float = 0.7, stop_strings: list = None) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop_strings: Strings that stop generation
            
        Returns:
            Generated text (prompt + completion)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id,
            stop_strings=stop_strings or ["```"],
            tokenizer=self.tokenizer
        )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text
    
    def get_info(self) -> dict:
        """Get model information."""
        if self.model is None:
            return {"status": "not_loaded"}
        
        return {
            "model_name": self.model_name,
            "model_key": self.model_key,
            "parameters": sum(p.numel() for p in self.model.parameters()),
            "device": str(self.model.device),
            "dtype": str(self.model.dtype)
        }
