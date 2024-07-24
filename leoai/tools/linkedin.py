from typing import List

from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser, JsonKeyOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from leoai.content import get_content_and_answer, find_content_for_query
from leoai.prompts import functions
from submind.llms.submind import SubmindModelFactory

LINKEDIN_INFO = """
Creating effective content for LinkedIn involves a multifaceted strategy that focuses on engaging
your target audience, utilizing various post formats, leveraging visuals, optimizing profiles, and
analyzing content performance.
### Key Components of a LinkedIn Content Strategy:
1. **Target Audience Identification**: Understanding the interests and preferences of your
audience is crucial for tailoring content that resonates with them. Creating detailed buyer
personas and engaging with different segments can enhance this process.
2. **Content Goals and Types**: Establishing clear objectives (e.g., brand awareness, lead
generation) and employing diverse content formats—such as articles, videos, infographics, and
polls—keeps the audience engaged and informed.
3. **Consistency and Value**: Posting regularly (2-3 times per week) while focusing on
value-driven content is essential to maintain visibility and foster engagement. Content should
provide insights and address industry news.
4. **Engagement and Community Building**: Encouraging interaction through questions,
discussions, and polls helps build a sense of community and enhances audience involvement.
5. **Analytics and Optimization**: Regularly reviewing performance metrics allows for
data-driven adjustments in strategy. Key metrics include engagement rates, impressions, and
conversions.
### Engaging Post Formats:
Utilizing various engaging formats, such as visual content (infographics, videos), storytelling,
polls, and carousel posts, can significantly enhance audience interaction. Compelling headlines
and formatting techniques (like subheadings and bullet points) also play a critical role in
maintaining reader interest.
### Leveraging Visuals:
High-quality visuals—such as infographics, slide decks, and branded graphics—are essential
for capturing attention and presenting complex information clearly. Tools like Canva and Adobe
Spark can facilitate the creation of eye-catching visuals, while maintaining a cohesive brand
identity is crucial for maximizing impact.
### Optimizing LinkedIn Profiles:
A well-optimized LinkedIn profile should include a professional headline, a compelling summary,
detailed experience, and showcased skills relevant to content creation. Engaging with your
network and regularly updating your profile keeps it current and visible.
### Analyzing Content Performance:
Effective analysis of LinkedIn content performance involves tracking key metrics, understanding
audience demographics, and utilizing tools like LinkedIn analytics and third-party platforms.

Regular reviews help identify successful content types and optimal posting times, while A/B
testing can optimize post effectiveness.
Overall, by integrating these strategies and continuously refining your approach based on
performance insights, you can cultivate a robust LinkedIn presence that enhances engagement
and supports broader marketing objectives.


"""

LINKEDIN_FORMATS ="""
For the last six months, I’ve been surveying every person that joins
this newsletter. And the results are pretty clear:
● 34.3% of you say growing a valuable audience is your biggest
challenge
● And 60.7% of you are using LinkedIn as your primary platform
So today I’m going to teach you four lesser-known strategies that you
can use to create valuable content and build your LinkedIn following.
Let’s dive in.
Strategy #1: The Value Add Commenter
You’ll see this strategy being talked about often on X/Twitter, also
known as being a “reply guy/girl”.
It refers to a person who is quick to comment and always has
something valuable to add to the conversation.
And this commenting strategy works wonders on LinkedIn too.
So instead of focusing entirely on your own posts, make it a habit to
leave a thoughtful comment on five to ten posts related your niche
every day.
But here's the key: “Agree, Justin! The sky is blue!” doesn’t count.

You have to make your comments so valuable that they could be a
standalone posts all by themselves.
It’s not easy. But it is worth the effort. Because smart commenting
positions you as an expert and naturally leads to more profile visits
and new followers.
To give this a try, simply use the "CEA" formula for your comments:
● Compliment the post
● Expand on one point with your own insights
● Ask a thought-provoking question to gain a reply
When you do this, you drastically increase your potential for being the
“most relevant” comment and (if the post goes viral) you can even
rack up hundreds of engagements and profile views.
Bonus Tip: Make sure your profile tagline is short enough to be read
on each comment so people know what you do. Keith left a great
comment that got some love, but his tagline cut off below so we don’t
get to see his offer.

Strategy #2: The Micro-Interview
Another way to grow your account is through collaboration.
You could reach out to three influencers in your niche every week for a
"micro-interview."
Ask them one specific, thought-provoking question related to their
expertise. And then share their response as a post, tagging them. This
is a great way to get a comment and some engagement from a big
account.
You’ll provide a ton of value to your audience, and your content will
get seen by the thousands (or hundreds of thousands) of people who
follow the person you interviewed.
Eddie Shleyner uses this technique very effectively.



Strategy #3: The Trend Translator
Being relevant and timely is one of the most powerful plays on social
media. And here’s a simple way to do this:
Set up Google Alerts for key topics in your industry. Then, when a
major news story breaks, be among the first to translate what it means
for your niche on LinkedIn.
You can use this simple formula to create trend translator posts:
"Breaking News + So What? + Now What?"
This recipe helps generate a ton of engagement around popular topics
and current events.
Strategy #4: The Contrarian Spotlight
People love contrarian takes because they’re sick and tired of reading
the same old recycled thought leadership. And you can take
advantage of that.
Once a week, find a popular opinion or trend in your industry that you
disagree with.
Create a post that respectfully challenges the popular opinion, and
back up your position with data and/or experience.

Here’s a format you follow:
● Popular opinion: [State the common view]
● Unpopular opinion: [Your contrarian take]
● Here's why: [3-5 bullet points with your reasoning]
● What do you think? [Encourage discussion]
This helps position you as a thought leader, sparks good debates, and
helps you stand out in a sea of plain vanilla content.
It also attracts followers who actually care about critical thinking and
fresh perspectives. And those are the types of people you want to
follow your account.
"""

LINKEDIN_PROMPT = """
    You are a powerful submind dedicated to writing compelling posts for LinkedIn.
    
    Your job is to write linkedin posts based on this topic: {topic}
    
    Here's what you should know about being a good linkedin writer: {info}
    
    Here are some good linkedin formats to use: {formats}
    
    Here's some context from content the user created about the topic: {context}
    
    Write 3-7 linkedin posts on the topic, using the context for details and the formats for structure.
    
    Think step by step and respond with your thoughts in <thinking></thinking> and the posts in <posts><post></post></posts>
"""


def write_linkedin_posts(query: str) -> List[str]:
    answer, content = find_content_for_query("linkedin")

    chat_model = SubmindModelFactory.get_mini("admin_mode", "leoai_chat")
    prompt = ChatPromptTemplate.from_template(LINKEDIN_PROMPT)
    chain = prompt | chat_model.bind(function_call={"name": "linkedin_posts"},
                                           functions=functions) | JsonOutputFunctionsParser()
    posts = chain.invoke({"topic": query, "context": answer, "info": LINKEDIN_INFO, "formats": LINKEDIN_FORMATS})
    thoughts = posts['thoughts']
    print(thoughts)
    return posts['posts']

