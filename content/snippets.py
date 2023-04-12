from search.models import Section


def create_snippet(section_id):
    section = Section.objects.filter(id=section_id).first()
    if not section:
        return
    if section.snippet:
        return section.snippet
    sections = Section.objects.filter(fulltext=section.fulltext).order_by("id").all()
    if len(sections) < 10:
        snippet = " ".join([section.text for section in sections])
    else:
        index = 0
        for i, s in enumerate(sections):
            if s.id == section.id:
                index = i
                break
        if index < 5:
            snippet = " ".join([section.text for section in sections[:10]])
        elif index > len(sections) - 6:
            snippet = " ".join([section.text for section in sections[-10:]])
        else:
            snippet = " ".join([section.text for section in sections[index - 5:index + 6]])
    section.snippet = snippet
    section.save()
    return snippet