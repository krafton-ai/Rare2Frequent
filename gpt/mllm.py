import requests
import json
import os
from transformers import AutoTokenizer
import transformers
import torch
import re
import torch
from transformers import LlamaForCausalLM, LlamaTokenizer
import ast

def GPT4(prompt,key):
    url = "https://api.openai.com/v1/chat/completions"
    api_key = key
    with open('../template/template.txt', 'r') as f:
        template=f.readlines()
    user_textprompt=f"Caption:{prompt} \n Let's think step by step:"
    
    textprompt= f"{' '.join(template)} \n {user_textprompt}"
    
    payload = json.dumps({
    "model": "gpt-4-1106-preview", # we suggest to use the latest version of GPT, you can also use gpt-4-vision-preivew, see https://platform.openai.com/docs/models/ for details. 
    "messages": [
        {
            "role": "user",
            "content": textprompt
        }
    ]
    })
    headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {api_key}',
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Content-Type': 'application/json'
    }
    print('waiting for GPT-4 response')
    response = requests.request("POST", url, headers=headers, data=payload)
    obj=response.json()
    text=obj['choices'][0]['message']['content']
    print(text)
    # Extract the split ratio and regional prompt

    return get_params_dict(text)


def local_llm(prompt,version,model_path=None):
    if model_path==None:
        model_id = "Llama-2-13b-chat-hf" 
    else:
        model_id=model_path
    print('Using model:',model_id)
    tokenizer = LlamaTokenizer.from_pretrained(model_id)
    model = LlamaForCausalLM.from_pretrained(model_id, load_in_8bit=False, device_map='auto', torch_dtype=torch.float16)
    with open('../template/template.txt', 'r') as f:
        template=f.readlines()
    user_textprompt=f"Caption:{prompt} \n Let's think step by step:"
    textprompt= f"{' '.join(template)} \n {user_textprompt}"
    model_input = tokenizer(textprompt, return_tensors="pt").to("cuda")
    model.eval()
    with torch.no_grad():
        print('waiting for LLM response')
        res = model.generate(**model_input, max_new_tokens=1024)[0]
        output=tokenizer.decode(res, skip_special_tokens=True)
        output = output.replace(textprompt,'')
    return get_params_dict(output)




def get_params_dict(output_text):
    response = output_text
    # Final split ratio
    split_ratio_match = re.search(r"Final split ratio: ([\d.,;]+)", response)
    if split_ratio_match:
        final_split_ratio = split_ratio_match.group(1)
        print("Final split ratio:", final_split_ratio)
    else:
        print("Final split ratio not found.")
    # Regional Prompt
    prompt_match = re.search(r"Regional Prompt: (.*?)(?=\n\n|\Z)", response, re.DOTALL)
    if prompt_match:
        regional_prompt = prompt_match.group(1).strip()
        print("Regional Prompt:", regional_prompt)
    else:
        print("Regional Prompt not found.")

    image_region_dict = {'Final split ratio': final_split_ratio, 'Regional Prompt': regional_prompt}    
    return image_region_dict


def GPT4_Rare2Frequent(prompt, key):
    
    obj_list = GPT4_DecomposeObject(prompt,key)
    print("obj_list: ", obj_list)

    result = {}
    for i, (obj_prompt, bbox) in enumerate(obj_list):
        
        output = GPT4_Rare2Frequent_single(obj_prompt, key)

        if len(output['r2f_prompt'][0]) == 1:
            result[f"obj{i+1}"] = {"freq": output['r2f_prompt'][0][0], "transition": output['visual_detail_level'], "bbox": bbox}
        elif len(output['r2f_prompt'][0]) == 2:
            result[f"obj{i+1}"] = {"freq": output['r2f_prompt'][0][0], "rare": output['r2f_prompt'][0][1], "transition": output['visual_detail_level'], "bbox": bbox}
        else:
            print(f'{i}-th object has more than two frequent prompts')

    result['base'] = {"freq": prompt}

    return result


def GPT4_DecomposeObject(prompt,key):
    print("*** call GPT4_DecomposeObject() ***")

    url = "https://api.openai.com/v1/chat/completions"
    api_key = key

    #with open('template/template_r2f_system.txt', 'r') as f:
    #    template_system=f.readlines()
    #    prompt_system=' '.join(template_system)

    with open('gpt/template/template_obj_user.txt', 'r') as f:
        template_user=f.readlines()
        template_user=' '.join(template_user)

    prompt_user = template_user.replace("{PROMPT}", prompt)
    
    payload = json.dumps({
    "model": "gpt-4", # we suggest to use the latest version of GPT, you can also use gpt-4-vision-preivew, see https://platform.openai.com/docs/models/ for details. 
    "messages": [
        {
            "role": "user",
            "content": prompt_user
        }
    ]
    })
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json'
    }
    print('waiting for GPT-4 response')
    response = requests.request("POST", url, headers=headers, data=payload)
    obj=response.json()
    
    text=obj['choices'][0]['message']['content']
    print(text)

    return get_params_dict_obj(text) # TODO: parsing


def get_params_dict_obj(response):

    obj_list = ast.literal_eval(response)
    return obj_list



def GPT4_Rare2Frequent_single(prompt, key):
    print("*** call GPT4_Rare2Frequent_single() ***")

    url = "https://api.openai.com/v1/chat/completions"
    api_key = key

    with open('gpt/template/template_r2f_system.txt', 'r') as f:
        template_system=f.readlines()
        prompt_system=' '.join(template_system)

    with open('gpt/template/template_r2f_user.txt', 'r') as f:
        template_user=f.readlines()
        template_user=' '.join(template_user)

    prompt_user=f"###Input: {prompt}\n###Output: "
    prompt_user= f"{template_user}\n\n{prompt_user}"
    
    payload = json.dumps({
    "model": "gpt-4", # we suggest to use the latest version of GPT, you can also use gpt-4-vision-preivew, see https://platform.openai.com/docs/models/ for details. 
    "messages": [
        {
            "role": "system",
            "content": prompt_system
        },
        {
            "role": "user",
            "content": prompt_user
        }
    ]
    })
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json'
    }
    print('waiting for GPT-4 response')
    response = requests.request("POST", url, headers=headers, data=payload)
    obj=response.json()
    
    text=obj['choices'][0]['message']['content']
    print(text)

    return get_params_dict_r2f(text) # TODO: parsing


def get_params_dict_r2f(response):
    
    visual_detail_level = response.split("###Visual Detail Level: ")[1].split("###Final Prompt Sequence:")[0].replace(' ', '').replace('\n', '')

    gpt_prompts = response.split("###Final Prompt Sequence: ")
    
    if len(gpt_prompts)>1:
        #print("Final Prompt Sequence:", gpt_prompts[-1])
        
        sep_prompt_sequence = gpt_prompts[-1].split(" SEP ")
        
        final_r2f_prompts = []
        for split_prompt in sep_prompt_sequence:
            split_prompt_sequence = split_prompt.split(" BREAK ")

            final_r2f_prompts.append(split_prompt_sequence)
    else:
        print("No rare concept.")
        final_r2f_prompts = [gpt_prompts]
    
    output = {'visual_detail_level': visual_detail_level, 'r2f_prompt': final_r2f_prompts}
    return output