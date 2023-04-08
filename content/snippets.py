from search.models import Section


def create_snippet(section_id):
    section = Section.objects.filter(id=section_id).first()
    if not section:
        return
    if section.snippet:
        return section.snippet
    sections = Section.objects.filter(fulltext=section.fulltext).order_by("id").all()
    # make snippet from 2 sections before and 2 sections after
    # if there are less than 5 sections, just use all of them
    # if there are less than 2 sections, just use the one section
    if len(sections) < 5:
        snippet = " ".join([section.text for section in sections])
    else:
        #get index of section id in sections
        index = 0
        for i, s in enumerate(sections):
            if s.id == section.id:
                index = i
                break
        if index < 2:
            snippet = " ".join([section.text for section in sections[:5]])
        elif index > len(sections) - 3:
            snippet = " ".join([section.text for section in sections[-5:]])
        else:
            snippet = " ".join([section.text for section in sections[index - 2:index + 3]])
    section.snippet = snippet
    section.save()
    return snippet