from fieldrouter import Routing, RoutingModel

__all__ = ("NestedModel",)


class NestedModel(RoutingModel):
    field_1: Routing(str, "a.aa.aaa.0")
    field_2: Routing(str, "a.aa.aaa.1")
    field_3: Routing(int, "b.bb.2")

def check():
    json_str = '{"a":{"aa":{"aaa":["value_1","value_2"]}},"b":{"bb":[3,4,5]}}'
    result = NestedModel.model_validate_json(json_str)

    result_dict = result.model_dump()
    print(result_dict)

    assert result_dict == {"field_1": "value_1", "field_2": "value_2", "field_3": 5}

if __name__ == "__main__":
    check()
