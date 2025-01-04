# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 23:49:32 2024

@author: olanr
"""


from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
import os
from groq import Groq
import json




load_dotenv()

groq = Groq()
openai_client = OpenAI()
        

class BasicResponse(BaseModel):
    expected_response: str

def get_gpt_response(text: str, context: str, response_format: BaseModel, openai_client: OpenAI = openai_client, temperature: float =1e-8)-> BaseModel:
    completion = openai_client.beta.chat.completions.parse(
      model="gpt-4o",
      messages=[
          {"role": "system", "content": context},
          {"role": "user", "content": text}
      ],
      response_format=response_format,
      temperature= temperature
    )

    response = completion.choices[0].message.parsed

    return response



def get_gpt_response_groq(text: str, context: str, response_model: BaseModel, openai_client: OpenAI = openai_client, temperature: float =1e-8)-> BaseModel:
    completion = groq.chat.completions.create(
      model="llama3-70b-8192",
      messages=[
          {"role": "system", "content": context},
          {"role": "user", "content": text}
      ],
      
      temperature= temperature,
      response_format = {"type": "json_object"}
    )

    return response_model.model_validate_json(completion.choices[0].message.content)


if __name__ == "__main__":
    text = "Explain the importance of fast language models"
    context = f"You are a helpful assistant that outputs responses in JSON. The JSON object must use the schema: {json.dumps(BasicResponse.model_json_schema(), indent=2)}"
    res1 = get_gpt_response_groq(text, context, BasicResponse)
