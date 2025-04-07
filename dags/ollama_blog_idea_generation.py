"""
This example consumes a list of products and produces a collection of blog ideas
"""

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

import airflow_ai_sdk as ai_sdk


@task
def get_products() -> list[dict]:
    """Get the list of products."""
    return [
        {"name": "Apache Airflow"},
        {"name": "Astronomer"},
        {"name": "Astro CLI"},
    ]


class BlogIdea(ai_sdk.BaseModel):
    name: str
    idea: str


@task.llm(
    model=OpenAIModel(
        model_name="llama3.1:8b",
        provider=OpenAIProvider(
            base_url="http://host.docker.internal:11434/v1"
        ),
    ),
    result_type=BlogIdea,
    system_prompt="""
    You are an experienced content strategist tasked with generating an engaging and informative blog idea based on a given product name. Given the product name provided, produce a compelling idea for a blog post.

    Return only the name and the idea.

    Product Name: [Insert Product Name Here]
    """,
)
def generate_blog_idea(product: dict | None = None):
    if product is None:
        raise AirflowSkipException("No product provided")

    return f"Product Name: {product['name']}"


@task
def display_blog_ideas(blog_ideas: list[BlogIdea]):
    """Display the list of generated blog ideas."""
    from pprint import pprint

    ideas_list = [{"product": idea['name'], "idea": idea['idea']} for idea in blog_ideas]
    pprint(ideas_list)

    return ideas_list


@dag(schedule=None, start_date=pendulum.datetime(2025, 3, 1, tz="UTC"), catchup=False)
def ollama_blog_idea_generation():
    products = get_products()
    blog_ideas = generate_blog_idea.expand(product=products)
    display_blog_ideas(blog_ideas)

ollama_blog_idea_generation_dag = ollama_blog_idea_generation()
if __name__ == "__main__":
    ollama_blog_idea_generation_dag.test()